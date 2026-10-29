// ───────────── PRUEBAS (no las edites) ─────────────
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Contador, ListaTareas } from "./03-estado.jsx";

const boton = (nombre) => screen.getByRole("button", { name: nombre });

describe("Contador", () => {
  it("empieza en 0", () => {
    render(<Contador />);
    expect(screen.getByText("Cuenta: 0")).toBeInTheDocument();
  });

  it("usa la prop `inicial`", () => {
    render(<Contador inicial={10} />);
    expect(screen.getByText("Cuenta: 10")).toBeInTheDocument();
  });

  it("«+1» suma 1 por cada click", async () => {
    const user = userEvent.setup();
    render(<Contador />);
    await user.click(boton("+1"));
    await user.click(boton("+1"));
    expect(screen.getByText("Cuenta: 2")).toBeInTheDocument();
  });

  it("«Reiniciar» vuelve al valor de `inicial`, no a 0", async () => {
    const user = userEvent.setup();
    render(<Contador inicial={5} />);
    await user.click(boton("+1"));
    expect(screen.getByText("Cuenta: 6")).toBeInTheDocument();
    await user.click(boton("Reiniciar"));
    expect(screen.getByText("Cuenta: 5")).toBeInTheDocument();
  });

  it("«+1 en 1 s» suma sobre el valor MÁS RECIENTE, no sobre uno viejo", async () => {
    const user = userEvent.setup();
    render(<Contador />);
    await user.click(boton("+1 en 1 s"));   // programa un +1 para dentro de 1 s
    await user.click(boton("+1"));
    await user.click(boton("+1"));          // mientras tanto el contador ya vale 2
    // tras 1 s debe valer 3 (2 + el +1 pendiente); con un valor viejo quedaría en 1
    expect(await screen.findByText("Cuenta: 3", {}, { timeout: 2500 })).toBeInTheDocument();
  });
});

describe("ListaTareas", () => {
  const entrada = () => screen.getByLabelText("Nueva tarea");
  const agregar = async (user, texto) => {
    await user.type(entrada(), texto);
    await user.click(boton("Agregar"));
  };

  it("empieza vacía", () => {
    render(<ListaTareas />);
    expect(screen.getByText("Pendientes: 0")).toBeInTheDocument();
    expect(screen.queryAllByRole("listitem")).toHaveLength(0);
  });

  it("«Agregar» crea la tarea, vacía el input y cuenta una pendiente", async () => {
    const user = userEvent.setup();
    render(<ListaTareas />);
    await agregar(user, "Leer");
    expect(screen.getByRole("checkbox", { name: "Leer" })).not.toBeChecked();
    expect(entrada()).toHaveValue("");
    expect(screen.getByText("Pendientes: 1")).toBeInTheDocument();
  });

  it("Enter también agrega (es un <form>)", async () => {
    const user = userEvent.setup();
    render(<ListaTareas />);
    await user.type(entrada(), "Estudiar{Enter}");
    expect(screen.getByRole("checkbox", { name: "Estudiar" })).toBeInTheDocument();
  });

  it("al enviar el formulario evita la recarga de la página (preventDefault)", async () => {
    const user = userEvent.setup();
    render(<ListaTareas />);
    let prevenido = null;
    document.addEventListener("submit", (e) => { prevenido = e.defaultPrevented; }, { once: true });
    await agregar(user, "Leer");
    expect(prevenido, "no se detectó un submit, o no llamaste a e.preventDefault()").toBe(true);
  });

  it("no agrega textos vacíos ni de solo espacios", async () => {
    const user = userEvent.setup();
    render(<ListaTareas />);
    await user.click(boton("Agregar"));
    await agregar(user, "   ");
    expect(screen.queryAllByRole("listitem")).toHaveLength(0);
    expect(screen.getByText("Pendientes: 0")).toBeInTheDocument();
  });

  it("recorta los espacios del texto", async () => {
    const user = userEvent.setup();
    render(<ListaTareas />);
    await agregar(user, "  Leer  ");
    expect(screen.getByRole("checkbox", { name: "Leer" })).toBeInTheDocument();
  });

  it("marcar y desmarcar recalcula «Pendientes»", async () => {
    const user = userEvent.setup();
    render(<ListaTareas />);
    await agregar(user, "A");
    await agregar(user, "B");
    expect(screen.getByText("Pendientes: 2")).toBeInTheDocument();
    await user.click(screen.getByRole("checkbox", { name: "A" }));
    expect(screen.getByRole("checkbox", { name: "A" })).toBeChecked();
    expect(screen.getByText("Pendientes: 1")).toBeInTheDocument();
    await user.click(screen.getByRole("checkbox", { name: "A" }));
    expect(screen.getByText("Pendientes: 2")).toBeInTheDocument();
  });

  it("«Borrar» quita esa tarea y deja las demás", async () => {
    const user = userEvent.setup();
    render(<ListaTareas />);
    await agregar(user, "A");
    await agregar(user, "B");
    await user.click(boton("Borrar A"));
    expect(screen.queryByRole("checkbox", { name: "A" })).not.toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: "B" })).toBeInTheDocument();
    expect(screen.getByText("Pendientes: 1")).toBeInTheDocument();
  });

  it("dos tareas con el mismo texto se borran de una en una (y sin keys repetidas)", async () => {
    const espia = vi.spyOn(console, "error").mockImplementation(() => {});
    const user = userEvent.setup();
    render(<ListaTareas />);
    await agregar(user, "Leer");
    await agregar(user, "Leer");
    expect(screen.getAllByRole("button", { name: "Borrar Leer" })).toHaveLength(2);
    await user.click(screen.getAllByRole("button", { name: "Borrar Leer" })[0]);
    expect(screen.getAllByRole("button", { name: "Borrar Leer" })).toHaveLength(1);
    expect(screen.getByText("Pendientes: 1")).toBeInTheDocument();
    const avisos = espia.mock.calls.map((c) => String(c[0])).join("\n");
    espia.mockRestore();
    expect(avisos, "React avisa de keys repetidas: usa un id único como key").not.toMatch(/same key|unique "key"/);
  });

  it("recibe `inicial` y NO muta ese arreglo al agregar ni al marcar", async () => {
    const user = userEvent.setup();
    const inicial = [{ id: 100, texto: "Previa", hecha: false }];
    render(<ListaTareas inicial={inicial} />);
    expect(screen.getByRole("checkbox", { name: "Previa" })).toBeInTheDocument();
    expect(screen.getByText("Pendientes: 1")).toBeInTheDocument();
    await agregar(user, "Nueva");
    await user.click(screen.getByRole("checkbox", { name: "Previa" }));
    expect(screen.getByText("Pendientes: 1")).toBeInTheDocument();
    expect(inicial).toEqual([{ id: 100, texto: "Previa", hecha: false }]);   // copiar, no modificar
  });

  it("la nota escrita en una fila se queda con SU fila al borrar otra (key estable)", async () => {
    const user = userEvent.setup();
    render(<ListaTareas />);
    await agregar(user, "A");
    await agregar(user, "B");
    await agregar(user, "C");
    await user.type(screen.getByLabelText("Nota de B"), "hola");
    await user.click(boton("Borrar A"));
    expect(screen.getByLabelText("Nota de B")).toHaveValue("hola");
    expect(screen.getByLabelText("Nota de C")).toHaveValue("");
  });
});
