# Local Model Responsibility Promotion — objetivo v4.3/v4.4

Una responsabilidad solo puede migrar a un modelo local mediante evaluación comparativa:

1. Un modelo supervisor de capacidad demostrada produce un resultado de referencia.
2. El modelo local ejecuta la misma tarea X veces con la misma entrada inicial.
3. Un evaluador explícito compara resultado, criterios y evidencia.
4. Shikamaru analiza instrucciones y logs; puede proponer cambios, nunca aplicarlos.
5. Tras aprobación humana se repite desde la entrada inicial, sin contexto oculto.
6. Solo si alcanza el umbral en todas las dimensiones se agrega la responsabilidad.
7. En caso contrario queda `more_tests_needed`.

Registrar tokens, costo, latencia, varianza, falsos positivos y regresiones. La promoción
es por familia/tarea específica, no por reputación general del modelo.
