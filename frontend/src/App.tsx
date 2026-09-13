import "./App.css";
import { LibraryDashboard } from "./pages/LibraryDashboard";
import { WhatToPlay } from "./pages/WhatToPlay";

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>Steam Backlog Coach</h1>
      </header>

      <main>
        <WhatToPlay />

        <section className="backlog-section">
          <h2>Your backlog</h2>
          <LibraryDashboard />
        </section>
      </main>
    </div>
  );
}

export default App;
