import { useEffect, useState } from "react";

export default function DonationsPage() {
    const [donators, setDonators] = useState<string>("Loading appreciation list...");

    useEffect(() => {
        fetch("https://raw.githubusercontent.com/xVapure/Noteab-Macro/refs/heads/main/assets/appreciation_list.txt")
            .then(res => res.text())
            .then(text => setDonators(text))
            .catch(err => setDonators("Unable to load appreciation list.\n" + err));
    }, []);

    return (
        <>
            <div className="page-header">
                <h2>Upstream Appreciation</h2>
                <p>Preserved acknowledgements for the original Coteab team</p>
            </div>

            <div className="card">
                <div className="card-header">
                    <div className="card-icon">💎</div>
                    <div>
                        <h3>Original Coteab support page</h3>
                        <p>Purchases here do not fund Reoteab</p>
                    </div>
                </div>

                <div style={{ padding: "0 15px 15px 15px", color: "var(--text-secondary)", lineHeight: "1.6" }}>
                    <p style={{ marginBottom: "12px" }}>
                        This page preserves the original Coteab team's donation information and donor acknowledgements for historical credit.
                    </p>
                    <p style={{ marginBottom: "12px" }}>
                        Reoteab does not manage the store, donor list, or upstream benefits.
                    </p>

                    <a
                        href="https://www.roblox.com/games/18203398779/Medival-castle#!/store"
                        target="_blank"
                        rel="noreferrer"
                        className="btn btn-accent"
                        style={{
                            width: "100%",
                            justifyContent: "center",
                            fontWeight: "bold",
                            textDecoration: "none",
                            display: "flex",
                            alignItems: "center"
                        }}
                    >
                        Visit Gamepass Store
                    </a>
                    <div style={{ textAlign: "center", marginTop: "8px", fontSize: "12px", opacity: 0.7 }}>
                        https://www.roblox.com/games/18203398779/Medival-castle#!/store
                    </div>
                </div>
            </div>

            <div className="card" style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: "300px" }}>
                <div className="card-header">
                    <div className="card-icon">🏆</div>
                    <div>
                        <h3>Donators Hall of Fame</h3>
                        <p>It automatically updates from GitHub</p>
                    </div>
                </div>

                <div style={{ padding: "15px", flex: 1, display: "flex", flexDirection: "column" }}>
                    <textarea
                        readOnly
                        value={donators}
                        style={{
                            flex: 1,
                            width: "100%",
                            resize: "none",
                            backgroundColor: "rgba(0,0,0,0.2)",
                            color: "var(--text-primary)",
                            border: "1px solid var(--border-color)",
                            borderRadius: "8px",
                            padding: "12px",
                            fontFamily: "monospace",
                            fontSize: "13px",
                            lineHeight: "1.5",
                            outline: "none"
                        }}
                    />
                </div>
            </div>
        </>
    );
}
