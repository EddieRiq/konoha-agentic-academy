"""Stdlib contract checks, not a general-purpose JSON Schema validator.

Exercise the Draft 2020-12 keywords used by these public data contracts against
real builders and malformed records. These are not provider output schemas.
"""
import copy
import json
import re
import tempfile
import unittest
from pathlib import Path

from tools.repo_evidence.acquire_repo_evidence import Authorization, acquire_repo_evidence
from tools.repo_evidence.study import build_repository_study, MAX_STUDY_ITEMS, MAX_STUDY_TEXT
from tools.repo_evidence.learning import self_improvement_recommendations, donor_learning
from tools.teachback.manage_teachback import start_repository_teachback, respond_repository_teachback

ROOT = Path(__file__).resolve().parents[2]
NAMES = ('repository_study_record', 'repository_teachback',
         'self_improvement_recommendations', 'donor_learning_recommendations')


def check(value, schema, root):
    """Assert this contract's subset; fail explicitly for unsupported keywords."""
    known = {'$schema', 'title', 'description', '$defs', '$ref', 'type', 'const', 'enum',
             'properties', 'required', 'additionalProperties', 'items', 'minItems', 'maxItems',
             'minLength', 'maxLength', 'pattern', 'minimum', 'maximum', 'oneOf', 'allOf',
             'if', 'then', 'else'}
    assert not set(schema) - known, set(schema) - known
    if '$ref' in schema:
        ref = schema['$ref']
        assert ref.startswith('#/$defs/')
        check(value, root['$defs'][ref.split('/')[-1]], root)
    if 'const' in schema:
        assert type(value) is type(schema['const']) and value == schema['const']
    if 'enum' in schema:
        assert any(type(value) is type(item) and value == item for item in schema['enum'])
    if 'type' in schema:
        types = schema['type'] if isinstance(schema['type'], list) else [schema['type']]
        mapping = {'object': dict, 'array': list, 'string': str, 'integer': int, 'boolean': bool, 'null': type(None)}
        assert any(type(value) is mapping[t] for t in types), (value, types)
    if isinstance(value, dict):
        assert set(schema.get('required', [])) <= set(value)
        props = schema.get('properties', {})
        if schema.get('additionalProperties') is False:
            assert set(value) <= set(props), set(value) - set(props)
        for key in value.keys() & props.keys():
            check(value[key], props[key], root)
    if isinstance(value, list):
        assert schema.get('minItems', 0) <= len(value) <= schema.get('maxItems', float('inf'))
        for item in value:
            if 'items' in schema:
                check(item, schema['items'], root)
    if isinstance(value, str):
        assert schema.get('minLength', 0) <= len(value) <= schema.get('maxLength', float('inf'))
        if 'pattern' in schema:
            assert re.search(schema['pattern'], value)
    if type(value) is int:
        assert schema.get('minimum', -float('inf')) <= value <= schema.get('maximum', float('inf'))
    if 'oneOf' in schema:
        matches = 0
        for branch in schema['oneOf']:
            try:
                check(value, branch, root)
                matches += 1
            except AssertionError:
                pass
        assert matches == 1, matches
    for branch in schema.get('allOf', []):
        check(value, branch, root)
    if 'if' in schema:
        try:
            check(value, schema['if'], root)
            condition = True
        except AssertionError:
            condition = False
        check(value, schema.get('then' if condition else 'else', {}), root)


class PublicSchemaContractsTests(unittest.TestCase):
    def setUp(self):
        self.schemas = {name: json.loads((ROOT / 'schemas/runtime' / (name + '.schema.json')).read_text()) for name in NAMES}
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)

    def fixture(self, name, rich=True):
        repo = self.base / name
        repo.mkdir()
        if rich:
            (repo / 'app.py').write_text('def action(): return 1\n')
            (repo / 'orphan.py').write_text(''.join(f'def unused_{i}(): return {i}\n' for i in range(15)))
            (repo / 'test_app.py').write_text('import app\ndef test_action(): pass\n')
            (repo / 'pyproject.toml').write_text('[project.scripts]\napp = "app:missing"\n')
            (repo / 'README.md').write_text('# Synthetic repository\n' + 'x' * 3000)
        pack = acquire_repo_evidence(repo, Authorization('human', 'synthetic public fixture'))
        study = build_repository_study(pack)
        session = start_repository_teachback(study)
        closed = respond_repository_teachback(session, study, ':entendido', actor='human')
        return pack, study, session, closed

    def valid(self, name, value):
        schema = self.schemas[name]
        check(value, schema, schema)

    def invalid(self, name, value):
        with self.assertRaises(AssertionError):
            self.valid(name, value)

    def test_required_keys_defined_and_known_objects_closed_recursively(self):
        def walk(node):
            if isinstance(node, dict):
                if 'required' in node:
                    self.assertLessEqual(set(node['required']), set(node.get('properties', {})))
                if node.get('type') == 'object':
                    self.assertIs(node.get('additionalProperties'), False)
                    self.assertTrue(node.get('properties'))
                if node.get('type') == 'array':
                    self.assertIn('items', node)
                    self.assertIn('maxItems', node)
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)
        for name, schema in self.schemas.items():
            with self.subTest(name=name):
                self.assertEqual(schema['$schema'], 'https://json-schema.org/draft/2020-12/schema')
                walk(schema)

    def test_study_and_teachback_real_outputs_and_malformed_shapes(self):
        pack, study, session, closed = self.fixture('study')
        self.valid('repository_study_record', study.as_dict())
        self.assertEqual(study.coverage['candidates']['included'], MAX_STUDY_ITEMS)
        self.assertTrue(study.coverage['candidates']['truncated'])
        for record in (session, closed, respond_repository_teachback(session, study, 'x' * 3000, actor='human')):
            self.valid('repository_teachback', record)
        for key, value in (('vcs', 'invented'), ('repo_root_id', 'bad'), ('extra', True)):
            record = study.as_dict()
            record['repository_identity'][key] = value
            self.invalid('repository_study_record', record)
        for mutate in (lambda r: r['coverage']['scan'].update(paths=-1),
                       lambda r: r['coverage']['tests'].update(included=MAX_STUDY_ITEMS + 1),
                       lambda r: r['coverage'].pop('components'),
                       lambda r: r['facts'][0].update(observation='x' * (MAX_STUDY_TEXT + 1)),
                       lambda r: r['facts'][0]['locator'].update(extra=True)):
            record = study.as_dict()
            mutate(record)
            self.invalid('repository_study_record', record)
        self.invalid('repository_teachback', {**session, 'completed_by_user': True})
        self.invalid('repository_teachback', {**closed, 'human_command': None})
        self.invalid('repository_teachback', {**session, 'last_question': 'x' * 2001})

    def test_recommendation_variants_from_production_and_rejection(self):
        pack, study, _, closed = self.fixture('self')
        ref = study.facts[0]['evidence_ref']
        good = {'evidence_refs': [ref] * 10, 'recommendation': 'x' * 3000, 'risk': 'risk', 'scope': 'scope'}
        for suggestions in ({}, [None, {'evidence_refs': ['invented']}, {'evidence_refs': [ref]}, good] * 3,
                            [good] * 12, []):
            report = self_improvement_recommendations(study, pack, closed, suggestions)
            self.valid('self_improvement_recommendations', report)
        report = self_improvement_recommendations(study, pack, closed, [good])
        self.assertEqual(len(report['validated']), 10)
        self.assertTrue(report['model_suggestions'][0]['text_truncated'])
        for partition in ('validated', 'model_suggestions'):
            for key in report[partition][0]:
                broken = copy.deepcopy(report)
                del broken[partition][0][key]
                self.invalid('self_improvement_recommendations', broken)
            broken = copy.deepcopy(report)
            broken[partition][0]['extra'] = True
            self.invalid('self_improvement_recommendations', broken)
        for suppressed in ([{'reason': 'invented'}], [{'reason': 'invalid_suggestion'}],
                           [{'reason': 'suggestion_limit', 'omitted': 0}],
                           [{'reason': 'suggestions_must_be_list', 'index': 0}]):
            self.invalid('self_improvement_recommendations', {**report, 'suppressed': suppressed})
        self.invalid('self_improvement_recommendations', {**report, 'limitations': [42]})
        broken = copy.deepcopy(report)
        broken['model_suggestions'][0]['provenance'][0]['locator']['line_start'] = 0
        self.invalid('self_improvement_recommendations', broken)

    def test_donor_comparisons_with_and_without_target_facts(self):
        dp, donor, _, dt = self.fixture('donor')
        for rich in (True, False):
            tp, target, _, tt = self.fixture('target-' + str(rich), rich)
            report = donor_learning(donor, dp, dt, target, tp, tt)
            self.valid('donor_learning_recommendations', report)
            self.assertTrue(report['recommendations'])
            for row in report['recommendations']:
                self.assertEqual('locator' in row['comparison_with_target']['provenance'], rich)
            for key in report['recommendations'][0]:
                broken = copy.deepcopy(report)
                del broken['recommendations'][0][key]
                self.invalid('donor_learning_recommendations', broken)
            for mutate in (lambda r: r['recommendations'][0].update(extra=True),
                           lambda r: r['recommendations'][0]['comparison_with_target'].update(extra=True),
                           lambda r: r['recommendations'][0]['comparison_with_target']['provenance'].update(evidence_ref='bad'),
                           lambda r: r.update(authorizes_action=True),
                           lambda r: r.update(source_url='x' * 2001)):
                broken = copy.deepcopy(report)
                mutate(broken)
                self.invalid('donor_learning_recommendations', broken)
