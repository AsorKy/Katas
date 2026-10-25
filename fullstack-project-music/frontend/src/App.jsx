import { useState } from "react";
import LoginForm from "./LoginForm";
import Me from "./Me";
import SongList from "./SongList";

export default function App() {
    const [token, setToken] = useState(null);

    return (
        <main>
            <h1>Music</h1>
              {token ? (
                  <>
                    <Me token={token} />
                    <button onClick={() => setToken(null)}>Salir</button>
                  </>
                ) : (
                  <LoginForm onLogin={setToken} />
              )}
            <SongList />
        </main>
    );
  }