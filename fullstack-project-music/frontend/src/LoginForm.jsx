import { useState } from "react"

const API = "http://localhost:8000";

export default function LoginForm({onLogin}) {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState(null);
    const [submitting, setSubmitting] = useState(false);

    async function handleSubmit(e) {
        e.preventDefault();
        setError(null);
        setSubmitting(true);
        try {
            const res = await fetch(`${API}/auth/login`, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({email, password})
            });
            if (res.status === 401) throw new Error("Correo o contrasena incorrectos");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            onLogin(data.access_token);
        } catch (err) {
            setError(err.message);
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <form onSubmit={handleSubmit}>
            <h2>Iniciar sesion</h2>
            <label>
                Correo
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </label>
            <label>
                Contraseña
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8}/>
            </label>
            <button type="submit" disabled={submitting}>
                {submitting ? "Entrando.." : "Entrar"}
            </button>
            {error && <p role="alert">{error}</p>}
        </form>
    );
}