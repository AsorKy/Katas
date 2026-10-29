# 04 · React: estado, render y efectos

> Un componente es una **función que recibe datos y devuelve pantalla**. Cuando los datos cambian, React vuelve a llamarla. Todo lo demás sale de ahí.

Reto: `react/retos/03-estado.jsx` · Recetas: R11 a R14

## La idea central

```
pantalla = componente(props, estado)
```

- **Props**: lo que te pasa quien te usa. Solo se leen (como los argumentos de una función).
- **Estado** (`useState`): lo que el componente recuerda entre renders (como un atributo de una clase de Python).
- **Render**: React llama a tu función otra vez, compara lo que devolvió con lo anterior y cambia en el navegador solo lo que difiere.

| Python | React |
|---|---|
| función que devuelve un string de HTML | componente que devuelve JSX |
| `self.n = 0` (atributo) | `const [n, setN] = useState(0)` |
| argumentos de la función | props |
| `[f(x) for x in xs]` | `{xs.map(x => <Fila key={x.id} … />)}` |
| `if` dentro de la plantilla | `{cond && <A/>}` o `{cond ? <A/> : <B/>}` |

## El estado es una foto fija

Dentro de un render, `n` **no cambia**. `setN` no modifica `n`: pide a React un render nuevo con otro valor.

```jsx
setN(n + 1);   // "ponlo en 1"
setN(n + 1);   // "ponlo en 1"   ← n sigue valiendo 0 en esta foto
setN(n + 1);   // "ponlo en 1"   → resultado: 1
console.log(n) // 0 (el valor viejo)
```

Cuando el valor nuevo **depende del anterior**, pasa una función. React la encadena con el último valor:

```jsx
setN((prev) => prev + 1);   // x3 → 3
```

El mismo problema aparece con `setTimeout` o `fetch`: la función guarda la foto vieja de `n`. Con la forma de función siempre sumas sobre el valor más reciente.

## Copiar, no modificar

React decide si re-renderizar comparando **referencias** (`Object.is`). Si modificas el arreglo y le pasas el mismo, para React no cambió nada.

```jsx
tareas.push(nueva);  setTareas(tareas);        // ✘ misma referencia
setTareas((ts) => [...ts, nueva]);             // ✔ agregar
setTareas((ts) => ts.map((t) => (t.id === id ? { ...t, hecha: !t.hecha } : t)));   // ✔ cambiar uno
setTareas((ts) => ts.filter((t) => t.id !== id));                                   // ✔ borrar
```

Ojo: el `push` a veces «parece funcionar» porque otro `setState` provoca el render. Es un bug dormido.

## Qué se rompe sin esto

1. `setN(n + 1)` varias veces o dentro de un `setTimeout`: suma menos de lo esperado.
2. Modificar el estado en el sitio: la pantalla no se actualiza (o solo a veces).
3. `key={índice}`: al borrar uno del medio, React reutiliza el estado de la fila equivocada.
4. `key` repetida o ausente: avisos en consola y filas mezcladas.
5. Guardar en estado lo que puedes calcular (por ejemplo `pendientes`): dos fuentes de verdad que se desincronizan.
6. Olvidar `e.preventDefault()` en un `<form>`: la página se recarga y pierdes el estado.
7. `useEffect` sin limpieza: respuestas viejas que pisan a las nuevas.

## Listas y `key`

La `key` le dice a React **quién es quién** entre renders. Debe ser **estable y única entre hermanos**: el `id` del dato. Nunca el índice si la lista puede cambiar de orden o borrar elementos.

## Formularios controlados

El estado es la única fuente de verdad del input:

```jsx
<input value={texto} onChange={(e) => setTexto(e.target.value)} />
```

Si pones `value` sin `onChange`, el input queda congelado. Usa `<form onSubmit>` para que Enter y el botón hagan lo mismo.

## Estado derivado

No lo guardes: **cálculalo** en cada render.

```jsx
const pendientes = tareas.filter((t) => !t.hecha).length;   // ✔
```

## useEffect

Corre **después** de pintar, y otra vez cuando cambia algo del arreglo de dependencias. Lo que devuelve es la **limpieza**: corre antes del siguiente efecto y al desmontar.

```jsx
useEffect(() => {
  const controller = new AbortController();
  fetch(`/api/tracks?q=${encodeURIComponent(q)}`, { signal: controller.signal })
    .then((r) => r.json())
    .then(setResultados)
    .catch((e) => { if (e.name !== "AbortError") setError(e); });
  return () => controller.abort();          // cancela la petición vieja
}, [q]);                                    // vuelve a correr si q cambia
```

- `[]` → una sola vez al montar. Sin arreglo → en cada render (casi siempre un error).
- Todo lo que el efecto usa de afuera (props, estado) va en las dependencias.
- Un objeto o función creados dentro del componente cambian en cada render: ponerlos en las dependencias provoca un bucle.
- En desarrollo con `<StrictMode>` cada efecto corre dos veces (montar, limpiar, montar) para destapar limpiezas olvidadas. En producción, una.
- **Condición de carrera**: sin limpieza, la respuesta de `"ab"` puede llegar después de la de `"abc"` y mostrar resultados viejos.

No necesitas un efecto para: calcular algo a partir del estado (hazlo en el render) ni para reaccionar a un click (hazlo en el manejador).

## Hooks propios

Una función cuyo nombre empieza por `use` y que usa otros hooks. Sirve para reutilizar lógica **con estado**:

```jsx
function useDebounce(valor, ms = 300) {
  const [lento, setLento] = useState(valor);
  useEffect(() => {
    const id = setTimeout(() => setLento(valor), ms);
    return () => clearTimeout(id);          // si valor cambia antes, se cancela
  }, [valor, ms]);
  return lento;
}
```

Reglas de los hooks: solo en el nivel superior de un componente o de otro hook (nunca dentro de un `if`, un bucle o una función anidada).

`useRef` guarda un valor que **no** provoca render, o apunta a un elemento del DOM (`ref.current`).

## Pregunta de entrevista → respuesta de una frase

- **¿Qué diferencia hay entre props y estado?** Las props vienen de fuera y no se modifican; el estado lo posee el componente y al cambiarlo se re-renderiza.
- **¿Por qué `setN(n + 1)` tres veces suma 1?** Porque `n` es una foto del render; usa `setN(prev => prev + 1)`.
- **¿Por qué no modificar el estado directamente?** React compara referencias; si no hay referencia nueva, no re-renderiza.
- **¿Para qué sirve la `key`?** Para que React identifique cada elemento entre renders; debe ser un id estable, no el índice.
- **¿Qué es un componente controlado?** Un input cuyo valor vive en el estado de React (`value` + `onChange`).
- **¿Cuándo corre `useEffect`?** Después del render, y otra vez cuando cambia algo de sus dependencias; su retorno es la limpieza.
- **¿Cómo evitas respuestas viejas en un buscador?** Limpieza del efecto con `AbortController` (y *debounce* para mandar menos peticiones).
- **¿Qué es un custom hook?** Una función `useAlgo` que reúne lógica con estado para reutilizarla.
