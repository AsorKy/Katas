// ───────────── PRUEBAS (no las edites) ─────────────
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Boton, Cuadricula, Tarjeta } from "./05-estilos.jsx";

let espia;
beforeEach(() => { espia = vi.spyOn(console, "error").mockImplementation(() => {}); });
afterEach(() => espia.mockRestore());
const avisos = () => espia.mock.calls.map((c) => c.map(String).join(" ").slice(0, 120));

describe("Boton", () => {
  it("es un <button type=\"button\"> con las clases «btn btn--primario» por defecto", () => {
    render(<Boton>Guardar</Boton>);
    const b = screen.getByRole("button", { name: "Guardar" });
    expect(b).toHaveAttribute("type", "button");
    expect(b.className).toBe("btn btn--primario");
    expect(avisos(), "React avisó de algo").toEqual([]);
  });

  it("la variante cambia la clase: «btn btn--secundario»", () => {
    render(<Boton variante="secundario">Cancelar</Boton>);
    expect(screen.getByRole("button").className).toBe("btn btn--secundario");
  });

  it("«is-activo» aparece solo con `activo`, sin «false», «undefined» ni espacios de más", () => {
    const { rerender } = render(<Boton activo>A</Boton>);
    expect(screen.getByRole("button").className).toBe("btn btn--primario is-activo");
    rerender(<Boton activo={false}>A</Boton>);
    expect(screen.getByRole("button").className).toBe("btn btn--primario");
    rerender(<Boton variante="secundario">A</Boton>);
    expect(screen.getByRole("button").className).toBe("btn btn--secundario");
    expect(avisos(), "React avisó de algo").toEqual([]);
  });

  it("`deshabilitado` deja el botón disabled y no llama a onClick; habilitado sí lo llama", async () => {
    const user = userEvent.setup();
    const alClick = vi.fn();
    const { rerender } = render(<Boton deshabilitado onClick={alClick}>Ok</Boton>);
    expect(screen.getByRole("button")).toBeDisabled();
    await user.click(screen.getByRole("button"));
    expect(alClick).not.toHaveBeenCalled();
    rerender(<Boton onClick={alClick}>Ok</Boton>);
    expect(screen.getByRole("button")).toBeEnabled();
    await user.click(screen.getByRole("button"));
    expect(alClick).toHaveBeenCalledTimes(1);
  });
});

describe("Tarjeta", () => {
  it("`ancho` (un número) se convierte en píxeles en el style en línea", () => {
    const { container } = render(<Tarjeta ancho={240}>Hola</Tarjeta>);
    const t = container.querySelector(".tarjeta");
    expect(t).not.toBeNull();
    expect(t).toHaveTextContent("Hola");
    expect(t).toHaveStyle({ width: "240px" });
    expect(avisos(), "React avisó de algo").toEqual([]);
  });

  it("`color` va en backgroundColor (camelCase) y sin avisos de React", () => {
    const { container } = render(<Tarjeta color="red">Hola</Tarjeta>);
    expect(container.querySelector(".tarjeta").style.backgroundColor).toBe("red");
    expect(avisos(), "React avisó de algo (¿camelCase? ¿style como objeto?)").toEqual([]);
  });

  it("sin `ancho` ni `color` no pone esos estilos", () => {
    const { container } = render(<Tarjeta>Hola</Tarjeta>);
    const t = container.querySelector(".tarjeta");
    expect(t.style.width).toBe("");
    expect(t.style.backgroundColor).toBe("");
  });
});

describe("Cuadricula", () => {
  it("por defecto: display grid, 3 columnas y hueco de 16 px; con props, las usa", () => {
    const { container, rerender } = render(<Cuadricula><span>a</span><span>b</span></Cuadricula>);
    const c = () => container.querySelector(".cuadricula");
    expect(c()).not.toBeNull();
    expect(c().children).toHaveLength(2);
    expect(c()).toHaveStyle({ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px" });
    rerender(<Cuadricula columnas={2} hueco={8}><span>a</span></Cuadricula>);
    expect(c()).toHaveStyle({ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "8px" });
    expect(avisos(), "React avisó de algo").toEqual([]);
  });
});
