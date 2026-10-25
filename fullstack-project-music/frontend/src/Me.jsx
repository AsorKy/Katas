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
                    if (error.name === "AbortError") return;
                    setError(e);
                } 
            }
        
            load();
            return () => controller.abort();
        }, 
        [token]
    );

    if (error) return <p role="alert">error</p>; 
    if (!me) return <p>Cargando perfil...</p>;
    return (
        <p>
            Session iniciada como <string>{me.email}</string>
        </p>
    );

}