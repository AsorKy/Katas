// Reto 04 · Los tres componentes típicos de una prueba técnica de React (75 min)
//
// Reglas del drill: a mano, sin IA, SIN abrir recetas.md ni la ficha. Cronometra.
// Resuelto cuando `npm run reto4` (dentro de react/) termine con todo en ✓.
// Ficha de apoyo (para después): ../../fichas/04-react-estado-y-efectos.md
//
// En todos los componentes, los DATOS llegan por una función que te pasan como prop (no hay red real):
// es lo que hace que sean fáciles de probar. Usa solo `useState` y `useEffect` (más el hook de abajo).
//
// ── a) <BuscadorCanciones buscar={fn} /> ────────────────────────────────────────────
//   buscar(texto, { signal }) es async y devuelve un arreglo de { id, title, artist }.
//   · Un <input> con la etiqueta «Buscar».
//   · DEBOUNCE: solo se busca cuando el usuario lleva 300 ms sin teclear. Escribe tu propio
//     hook `useDebounce(valor, ms)` dentro de este archivo.
//   · Si el texto está vacío (o solo espacios): NO se llama a buscar y se muestra «Escribe para buscar».
//   · Se llama a buscar(texto, { signal }) con el texto tal cual y una señal de un AbortController.
//   · Mientras espera:  <p>Cargando…</p>
//   · Si devuelve [] :   <p>Sin resultados</p>
//   · Si rechaza:        <p role="alert">Error: <mensaje del error></p>
//   · Si devuelve datos: una <ul> con un <li> por canción, con el texto  «título — artista»  (raya larga —).
//   · CARRERA: si el usuario cambia el texto, la búsqueda anterior se CANCELA (signal.abort()) y su
//     respuesta nunca se muestra, aunque `buscar` no haga caso de la señal y responda tarde.
//     Una búsqueda cancelada NO es un error: no se muestra ninguna alerta.
//   · Al desmontar el componente se cancela la búsqueda en curso.
//
// ── b) <ListaPaginada cargar={fn} porPagina={3} /> ──────────────────────────────────
//   cargar(pagina) es async (la página 1 es la primera) y devuelve { items, total }, donde items son
//   { id, title, artist } de ESA página y total es el número de canciones de todo el catálogo.
//   · Carga la página 1 al montar.
//   · Un botón «Anterior», un texto «Página N de M» y un botón «Siguiente».
//     M = cantidad de páginas = total / porPagina redondeado hacia ARRIBA; nunca menos de 1.
//     Antes de la primera respuesta, el total se considera 0 (se ve «Página 1 de 1»).
//   · «Anterior» está deshabilitado en la página 1; «Siguiente» en la última página.
//   · Al pulsar un botón, N cambia de inmediato y se pide esa página.
//   · MIENTRAS carga: se ve <p>Cargando…</p>, NO se ven las canciones de la página anterior
//     y los dos botones de página están deshabilitados.
//   · Cuando termina: una <ul> con un <li> por canción, «título — artista».
//   · Si cargar rechaza: <p role="alert">Error: <mensaje></p> y un botón «Reintentar» que vuelve a
//     pedir la MISMA página.
//
// ── c) <DetalleCancion id={n} cargar={fn} /> ────────────────────────────────────────
//   cargar(id) es async y devuelve { id, title, artist, year }. (Aquí NO recibes señal.)
//   · Carga al montar y cada vez que `id` CAMBIA. Con el mismo id no vuelve a pedir.
//   · Mientras carga: <p>Cargando…</p> (también al cambiar de id: no se dejan los datos del id anterior).
//   · Con datos:  <h2>título</h2>  y  <p>artista · año</p>   (punto medio ·)
//   · Si rechaza: <p role="alert">Error: <mensaje></p>
//   · Si `id` cambia varias veces seguidas, solo se muestra la respuesta del ÚLTIMO id, aunque
//     las respuestas viejas lleguen más tarde.

import { useEffect, useState } from "react";

// ───────────── TU CÓDIGO ─────────────

export function DetalleCancion({id, cargar}) {
  const [cancion, setCancion] = useState(null);
  const [error, setError] = useState(null);
  const [cargando, setCargando] = useState(true);

  useEffect(
    () => {
      let ignorar = false
      setCargando(true);
      setError(null);
      setCancion(null);
      cargar(id)
        .then((datos) => {if (!ignorar) setCancion(datos);})
        .catch((e) => {if (!ignorar) setError(e);})
        .finally(() => {if (!ignorar) setCargando(false);});
      return () => {ignorar = true;};
    },[id]
  );

  if (cargando) return <p>Cargando…</p>;
  if (error) return <p role="alert">Error: {error.message}</p>;
  return(
    <div>
      <h2>{cancion.title}</h2>
      <p>{cancion.artist} · {cancion.year} </p>
    </div>
  )

};


export function ListaPaginada({ cargar, porPagina = 3 }) {
  const [pagina, setPagina] = useState(1);
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);
  const [intento, setIntento] = useState(0);

  useEffect(
    () => {
      let ignorar =false;
      setError(null);
      setCargando(true);
      cargar(pagina)
        .then((r) => { if (!ignorar) { setItems(r.items); setTotal(r.total); } })
        .catch((e) => { if (!ignorar) setError(e); })
        .finally(() => { if (!ignorar) setCargando(false); });
      return () => {ignorar = true;};
    }
    ,[pagina, intento]
  );

  const totalPaginas = Math.max(1, Math.ceil(total/porPagina));

  return (
    <div>
      <button onClick={() => setPagina((p) => p - 1)} disabled={cargando || pagina <=1}> Anterior </button>
      <span>Página {pagina} de {totalPaginas}</span>
      <button onClick={()=> setPagina((p) => p + 1)} disabled={cargando || pagina>=totalPaginas}>Siguiente</button>

      {cargando && <p>Cargando…</p>}
      {error && (
        <>
          <p role="alert">Error: {error.message}</p>
          <button onClick={() => setIntento((intento) => intento + 1)}>Reintentar</button>
        </>
      )}
      {!cargando && !error && (
        <ul>
          {items.map(
            (c) => <li key={c.id}>{c.title} — {c.artist}</li>
          )}
        </ul>
      )}

    </div>
  )

}



function useDebounce(valor, ms=300){
  const [lento, setLento] = useState(valor);
  useEffect(
    () => {
      const id = setTimeout(() => setLento(valor), ms);
      return () => clearTimeout(id);
    },
    [valor, ms]
  );
  return lento
};

export function BuscadorCanciones({ buscar }) {
  // ── 1. ESTADO (lo que cambia y debe redibujar) ──
  const [texto, setTexto] = useState("");
  const [resultados, setResultados] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);

  // ── 2. DERIVADO (se calcula en el render, no es estado) ──
  const textoFinal = useDebounce(texto,300);
  const hayConsulta = textoFinal.trim() !== "";

  // ── 3. EFECTO DE BÚSQUEDA ── depende de [textoFinal], NO de [texto]
  useEffect(()=>{
    if (!hayConsulta) {
      // no se busca: deja todo limpio (resultados, cargando, error)
      setResultados([]);
      setCargando(false);
      setError(null);
      return;
    }

    const controller = new AbortController();

    // empieza a cargar y borra el error anterior
    setCargando(true);
    setError(null);

    buscar(textoFinal, {signal: controller.signal})
      .then((r) => {if (!controller.signal.aborted) setResultados(r);})
      .catch((e) => {if (!controller.signal.aborted) setError(e);})
      .finally(() => { if (!controller.signal.aborted) setCargando(false); });

    return () => controller.abort();

  }, [textoFinal]);

  // ── 4. RENDER ──

  return (
    <div>
      <label>
        Buscar
        <input value={texto} onChange={(e) => setTexto(e.target.value)} />
      </label>
      {!hayConsulta && <p>Escribe para buscar</p>}
      {hayConsulta && cargando && <p>Cargando…</p>}
      {hayConsulta && error && <p role="alert">Error: {error.message}</p>}
      {hayConsulta && !cargando && !error && (
        resultados.length ===0
        ? <p>Sin resultados</p>
        : (
          <ul>
            {resultados.map(
              (c) => (
                <li key={c.id}>{c.title} — {c.artist}</li>
              )
            )}
          </ul>
        )
      )}
    </div>
  );
};

