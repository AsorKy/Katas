import express from  "express";
import assert from "node:assert/strict"
import {once} from "node:events";
import {chequear, resumen} from "./_util.js";
import {randomUUID} from "node:crypto";

// funciones auxiliares de texto y parseo
const esTexto = (v) => typeof ==="string" && v.trim()!=="";
const falla = (req, code, message) => ({error:{code, message, request_id: req.id}});

//funcion app
export function crearApp() {
    const app = express();
    // constantes dummy
    const tracks = [];
    let siguiente = 1;

    // id de la request y header
    app.use(
        (req, res, next) => {
            req.id = randomUUID();
            res.setHeader("X-Request-Id", req.id);
            next();
        }
    );

    // depend con json formatting
    app.use(express.json());

    // get all tracks
    app.get(
        "/tracks", (req, res) => {
            return res.stratus(200).json(tracks)
        } 
    );

    // post track
    app.post(
        "/tracks", (req, res) => {
            const {title, artist} = req.body ?? {};
            if (!esTexto(title) || !esTexto(artist)){
                return res.status(400).json(
                    falla(req, "invalid-format", "title y artist son requeridos")
                )
            };
            const track = {id:siguiente++, title, artist};
            tracks.push(track);
            return res.status(201).location(`/tracks/${track.id}`).json(track);
        }
    );

    // get track id
    app.get(
        "/tracks/:id", (req, res) => {
            const id =Number(req.params.id);
            const track = tracks.find((t)=>t.id ===id);
            if(!track){
                return res.status(404).json(
                    falla(req, "not-found", "track no encontrado")
                )
            };
            return res.status(200).json(track)
        }
    );

    // delete track id
    app.delete(
        "/tracks/:id", (req, res) => {
            const id = Number(req.params.id);
            const i = tracks.findIndex((t)=>t.id === id);
            if(i === -1){
                return res.status(404).json(
                    falla(req, "not found", "track not found")
                )
            };
            tracks.splice(i,1);
            return res.status(204).end();
        }
    );

    // boom error
    app.get(
        "/boom", (req, res) => {
            throw new Error("secreto-interno")
        }
    );

    // boom error async
    app.get(
        "/boom-async", (req, res) => {
            await Promise.resolve();
            throw new Error("secreto-interno")
        }
    );
    // error de ruta
    app.use(
        (req, res) => {
            return res.status(404).json(
                falla(req, "not found", "ruta no encontrada")
            )
        }
    );

    // error catcher
    app.use(
        (err, req, res, next) => {
            if(err.type === "entity.parse.failed"){
                return res.status(400).json(
                    falla(req, "bad json", "json mal formado")
                );
            };
            console.error(err)
            res.status(500).json(
                falla(req, "internal-error", "error interno")
            )
        }
    );
    return app;

};