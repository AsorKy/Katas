// ───────────── PRUEBAS (no las edites) ─────────────
import { describe, expect, it, vi } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BuscadorCanciones, DetalleCancion, ListaPaginada } from "./04-componentes-tipicos.jsx";

// ── ayudas ──
const esperar = (ms) => act(() => new Promise((r) => setTimeout(r, ms)));

function diferido() {
  let resolver, rechazar;
  const promesa = new Promise((res, rej) => { resolver = res; rechazar = rej; });
  promesa.catch(() => {});     // evita avisos de «rechazo sin manejar» del propio arnés
  return { promesa, resolver, rechazar };
}
const resolverEn = (d, valor) => act(async () => { d.resolver(valor); });
const rechazarEn = (d, error) => act(async () => { d.rechazar(error); });

// `buscar` falso: cada llamada queda registrada y se resuelve a mano.
// respetaSenal=true  → como fetch: al cancelar, rechaza con AbortError.
// respetaSenal=false → un servicio que ignora la señal y responde tarde.
function buscadorControlado({ respetaSenal = true } = {}) {
  const llamadas = [];
  const buscar = vi.fn((q, opciones) => {
    const d = diferido();
    const signal = opciones?.signal;
    llamadas.push({ q, signal, ...d });
    if (respetaSenal && signal) {
      signal.addEventListener("abort", () => d.rechazar(new DOMException("Aborted", "AbortError")));
    }
    return d.promesa;
  });
  return { buscar, llamadas };
}

const escribir = (user, texto) => user.type(screen.getByLabelText("Buscar"), texto);
const llamadasHechas = (llamadas, n) =>
  waitFor(() => expect(llamadas).toHaveLength(n), { timeout: 1500 });

const CANCIONES = Array.from({ length: 7 }, (_, i) => ({ id: i + 1, title: `Tema ${i + 1}`, artist: "Ana" }));

// ───────────────────────── a) Buscador ─────────────────────────
describe("BuscadorCanciones", () => {
  it("con el campo vacío o de solo espacios no llama a buscar y pide escribir", async () => {
    const { buscar } = buscadorControlado();
    const user = userEvent.setup();
    render(<BuscadorCanciones buscar={buscar} />);
    expect(screen.getByText("Escribe para buscar")).toBeInTheDocument();
    await escribir(user, "   ");
    await esperar(450);
    expect(buscar).not.toHaveBeenCalled();
    expect(screen.getByText("Escribe para buscar")).toBeInTheDocument();
  });

  it("debounce: espera 300 ms sin teclear y llama UNA vez, con el texto final y una señal", async () => {
    const { buscar, llamadas } = buscadorControlado();
    const user = userEvent.setup();
    render(<BuscadorCanciones buscar={buscar} />);
    await escribir(user, "abc");
    expect(buscar, "se llamó antes de que pasaran 300 ms sin teclear").not.toHaveBeenCalled();
    await llamadasHechas(llamadas, 1);
    expect(llamadas[0].q).toBe("abc");
    expect(llamadas[0].signal).toBeInstanceOf(AbortSignal);
    await esperar(450);
    expect(buscar).toHaveBeenCalledTimes(1);
  });

  it("muestra «Cargando…» y después la lista «título — artista»", async () => {
    const { buscar, llamadas } = buscadorControlado();
    const user = userEvent.setup();
    render(<BuscadorCanciones buscar={buscar} />);
    await escribir(user, "ab");
    expect(await screen.findByText("Cargando…", {}, { timeout: 1500 })).toBeInTheDocument();
    await resolverEn(llamadas[0], [
      { id: 1, title: "Intro", artist: "Ana" },
      { id: 2, title: "Final", artist: "Beto" },
    ]);
    expect(await screen.findByText("Intro — Ana")).toBeInTheDocument();
    expect(screen.getByText("Final — Beto")).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    expect(screen.queryByText("Cargando…")).not.toBeInTheDocument();
  });

  it("si no hay coincidencias muestra «Sin resultados»", async () => {
    const { buscar, llamadas } = buscadorControlado();
    const user = userEvent.setup();
    render(<BuscadorCanciones buscar={buscar} />);
    await escribir(user, "zzz");
    await llamadasHechas(llamadas, 1);
    await resolverEn(llamadas[0], []);
    expect(await screen.findByText("Sin resultados")).toBeInTheDocument();
    expect(screen.queryByRole("listitem")).not.toBeInTheDocument();
  });

  it("si buscar rechaza muestra una alerta «Error: <mensaje>»", async () => {
    const { buscar, llamadas } = buscadorControlado();
    const user = userEvent.setup();
    render(<BuscadorCanciones buscar={buscar} />);
    await escribir(user, "ab");
    await llamadasHechas(llamadas, 1);
    await rechazarEn(llamadas[0], new Error("boom"));
    expect(await screen.findByRole("alert")).toHaveTextContent("Error: boom");
    expect(screen.queryByText("Cargando…")).not.toBeInTheDocument();
  });

  it("carrera: la búsqueda vieja se cancela y su respuesta tardía no pisa a la nueva (aunque `buscar` ignore la señal)", async () => {
    const { buscar, llamadas } = buscadorControlado({ respetaSenal: false });
    const user = userEvent.setup();
    render(<BuscadorCanciones buscar={buscar} />);
    await escribir(user, "a");
    await llamadasHechas(llamadas, 1);
    await escribir(user, "b");                       // el texto ahora es «ab»
    await llamadasHechas(llamadas, 2);
    expect(llamadas[1].q).toBe("ab");
    expect(llamadas[0].signal.aborted, "la búsqueda vieja debe cancelarse con abort()").toBe(true);
    expect(llamadas[1].signal.aborted).toBe(false);
    await resolverEn(llamadas[1], [{ id: 2, title: "Nuevo", artist: "X" }]);
    await resolverEn(llamadas[0], [{ id: 1, title: "Viejo", artist: "Y" }]);   // llega tarde
    await esperar(50);
    expect(screen.getByText("Nuevo — X")).toBeInTheDocument();
    expect(screen.queryByText("Viejo — Y"), "se mostró la respuesta de la búsqueda vieja").not.toBeInTheDocument();
  });

  it("cancelar no es un error, y al desmontar se cancela la búsqueda en curso", async () => {
    const { buscar, llamadas } = buscadorControlado();    // esta vez `buscar` rechaza con AbortError al cancelar
    const user = userEvent.setup();
    const { unmount } = render(<BuscadorCanciones buscar={buscar} />);
    await escribir(user, "a");
    await llamadasHechas(llamadas, 1);
    await escribir(user, "b");
    await llamadasHechas(llamadas, 2);
    await esperar(50);
    expect(llamadas[0].signal.aborted).toBe(true);
    expect(screen.queryByRole("alert"), "una búsqueda cancelada no debe mostrarse como error").not.toBeInTheDocument();
    expect(screen.getByText("Cargando…")).toBeInTheDocument();
    unmount();
    expect(llamadas[1].signal.aborted, "al desmontar hay que cancelar la búsqueda en curso").toBe(true);
  });
});

// ───────────────────────── b) Lista paginada ─────────────────────────
describe("ListaPaginada", () => {
  const cargarCatalogo = (n, porPagina = 3) =>
    vi.fn(async (p) => ({ items: CANCIONES.slice(0, n).slice((p - 1) * porPagina, p * porPagina), total: n }));
  const boton = (nombre) => screen.getByRole("button", { name: nombre });

  it("carga la página 1 al montar: «Cargando…», luego 3 canciones y «Página 1 de 3»", async () => {
    const d = diferido();
    const cargar = vi.fn(() => d.promesa);
    render(<ListaPaginada cargar={cargar} porPagina={3} />);
    expect(screen.getByText("Cargando…")).toBeInTheDocument();
    expect(cargar).toHaveBeenCalledTimes(1);
    expect(cargar).toHaveBeenCalledWith(1);
    await resolverEn(d, { items: CANCIONES.slice(0, 3), total: 7 });
    expect(await screen.findByText("Tema 1 — Ana")).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(3);
    expect(screen.getByText("Página 1 de 3")).toBeInTheDocument();
    expect(screen.queryByText("Cargando…")).not.toBeInTheDocument();
  });

  it("«Siguiente» pide la página 2 y cambia el número de inmediato; «Anterior» vuelve", async () => {
    const cargar = cargarCatalogo(7);
    const user = userEvent.setup();
    render(<ListaPaginada cargar={cargar} porPagina={3} />);
    await screen.findByText("Tema 1 — Ana");
    expect(boton("Anterior")).toBeDisabled();
    expect(boton("Siguiente")).toBeEnabled();
    await user.click(boton("Siguiente"));
    expect(screen.getByText("Página 2 de 3")).toBeInTheDocument();
    expect(await screen.findByText("Tema 4 — Ana")).toBeInTheDocument();
    expect(cargar).toHaveBeenLastCalledWith(2);
    expect(boton("Anterior")).toBeEnabled();
    await user.click(boton("Anterior"));
    expect(screen.getByText("Página 1 de 3")).toBeInTheDocument();
    expect(await screen.findByText("Tema 1 — Ana")).toBeInTheDocument();
  });

  it("cuenta bien las páginas: 7 → 3 (la última con 1), 6 → 2, 0 → «Página 1 de 1»", async () => {
    const user = userEvent.setup();
    const siete = render(<ListaPaginada cargar={cargarCatalogo(7)} porPagina={3} />);
    await screen.findByText("Tema 1 — Ana");
    await user.click(boton("Siguiente"));
    await screen.findByText("Tema 4 — Ana");
    await user.click(boton("Siguiente"));
    expect(await screen.findByText("Tema 7 — Ana")).toBeInTheDocument();
    expect(screen.getByText("Página 3 de 3")).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(1);
    expect(boton("Siguiente"), "en la última página «Siguiente» debe estar deshabilitado").toBeDisabled();
    siete.unmount();

    const seis = render(<ListaPaginada cargar={cargarCatalogo(6)} porPagina={3} />);
    expect(await screen.findByText("Página 1 de 2")).toBeInTheDocument();
    seis.unmount();

    render(<ListaPaginada cargar={cargarCatalogo(0)} porPagina={3} />);
    await waitFor(() => expect(screen.queryByText("Cargando…")).not.toBeInTheDocument());
    expect(screen.getByText("Página 1 de 1")).toBeInTheDocument();
    expect(boton("Anterior")).toBeDisabled();
    expect(boton("Siguiente")).toBeDisabled();
  });

  it("mientras carga otra página: «Cargando…», sin las canciones viejas y con los botones deshabilitados", async () => {
    const d2 = diferido();
    const cargar = vi.fn((p) => (p === 1 ? Promise.resolve({ items: CANCIONES.slice(0, 3), total: 7 }) : d2.promesa));
    const user = userEvent.setup();
    render(<ListaPaginada cargar={cargar} porPagina={3} />);
    await screen.findByText("Tema 1 — Ana");
    await user.click(boton("Siguiente"));
    expect(screen.getByText("Cargando…")).toBeInTheDocument();
    expect(screen.queryByText("Tema 1 — Ana"), "se ven canciones de la página anterior mientras carga").not.toBeInTheDocument();
    expect(boton("Anterior")).toBeDisabled();
    expect(boton("Siguiente")).toBeDisabled();
    await resolverEn(d2, { items: CANCIONES.slice(3, 6), total: 7 });
    expect(await screen.findByText("Tema 4 — Ana")).toBeInTheDocument();
    expect(screen.queryByText("Cargando…")).not.toBeInTheDocument();
  });

  it("si cargar rechaza muestra la alerta y «Reintentar» pide de nuevo la MISMA página", async () => {
    const d1 = diferido();
    const d2 = diferido();
    const cargar = vi.fn().mockReturnValueOnce(d1.promesa).mockReturnValueOnce(d2.promesa);
    const user = userEvent.setup();
    render(<ListaPaginada cargar={cargar} porPagina={3} />);
    await rechazarEn(d1, new Error("falló"));
    expect(await screen.findByRole("alert")).toHaveTextContent("Error: falló");
    await user.click(boton("Reintentar"));
    expect(cargar).toHaveBeenCalledTimes(2);
    expect(cargar).toHaveBeenLastCalledWith(1);
    expect(screen.getByText("Cargando…")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    await resolverEn(d2, { items: CANCIONES.slice(0, 3), total: 7 });
    expect(await screen.findByText("Tema 1 — Ana")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reintentar" })).not.toBeInTheDocument();
  });
});

// ───────────────────────── c) Detalle ─────────────────────────
describe("DetalleCancion", () => {
  const cancion = (id) => ({ id, title: `Tema ${id}`, artist: "Ana", year: 2000 + id });

  it("carga al montar, muestra los datos y no vuelve a pedir con el mismo id", async () => {
    const d = diferido();
    const cargar = vi.fn(() => d.promesa);
    const { rerender } = render(<DetalleCancion id={1} cargar={cargar} />);
    expect(screen.getByText("Cargando…")).toBeInTheDocument();
    expect(cargar).toHaveBeenCalledWith(1);
    await resolverEn(d, cancion(1));
    expect(await screen.findByRole("heading", { name: "Tema 1" })).toBeInTheDocument();
    expect(screen.getByText("Ana · 2001")).toBeInTheDocument();
    rerender(<DetalleCancion id={1} cargar={cargar} />);
    expect(cargar, "con el mismo id no debe volver a pedir").toHaveBeenCalledTimes(1);
  });

  it("si cargar rechaza muestra «Error: <mensaje>» en una alerta", async () => {
    const d = diferido();
    render(<DetalleCancion id={1} cargar={() => d.promesa} />);
    await rechazarEn(d, new Error("no existe"));
    expect(await screen.findByRole("alert")).toHaveTextContent("Error: no existe");
    expect(screen.queryByText("Cargando…")).not.toBeInTheDocument();
  });

  it("al cambiar `id` vuelve a cargar y no deja los datos del id anterior", async () => {
    const cargar = vi.fn(async (id) => cancion(id));
    const { rerender } = render(<DetalleCancion id={1} cargar={cargar} />);
    expect(await screen.findByRole("heading", { name: "Tema 1" })).toBeInTheDocument();
    rerender(<DetalleCancion id={2} cargar={cargar} />);
    expect(cargar).toHaveBeenLastCalledWith(2);
    expect(screen.getByText("Cargando…")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Tema 1" })).not.toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Tema 2" })).toBeInTheDocument();
  });

  it("carrera: si la respuesta del id 1 llega después de pedir el 2, no se muestra", async () => {
    const d1 = diferido();
    const d2 = diferido();
    const cargar = vi.fn((id) => (id === 1 ? d1.promesa : d2.promesa));
    const { rerender } = render(<DetalleCancion id={1} cargar={cargar} />);
    rerender(<DetalleCancion id={2} cargar={cargar} />);
    await resolverEn(d2, cancion(2));
    expect(await screen.findByRole("heading", { name: "Tema 2" })).toBeInTheDocument();
    await resolverEn(d1, cancion(1));                      // llega tarde
    await esperar(50);
    expect(screen.getByRole("heading", { name: "Tema 2" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Tema 1" }), "se mostró la respuesta de un id viejo").not.toBeInTheDocument();
  });
});
