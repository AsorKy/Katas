import {useEffect, useState} from "react";

const API = "http://localhost:8000";

export default function Me({token}) {
    const [me, setMe] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
            const controller = new AbortController();

            async function load() {
                try {
                    const res = await fetch(`${API}/me`, {
                        headers: { Authorization: `Bearer ${token}`},
                        signal: controller.signal,
                    });
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    setMe(await res.json());
                } catch (e){
                    if (e.name === "AbortError") return;
                    setError(e.message);
                } 
            }
        
            load();
            return () => controller.abort();
        }, 
        [token]
    );

    if (error) return <p role="alert">Error: {error}</p>; 
    if (!me) return <p>Cargando perfil...</p>;
    return (
        <p>
            Sesión iniciada como <strong>{me.email}</strong>
        </p>
    );

}