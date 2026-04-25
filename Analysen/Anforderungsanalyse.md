# 1. Anforderungsanalyse 

## 1.1 Informelle Beschreibung

Das betrachtete Problem ist eine kombinatorische Optimierungsaufgabe aus dem Bereich der Einkaufs- bzw. Ressourcenoptimierung.Ziel des Systems ist es, automatisch eine möglichst optimale Kombination von Produkten auszuwählen, sodass unter einem gegebenen Budget ein maximaler Nutzen in Form von Protein erreicht wird. Dabei soll der Algorithmus aus einer Menge diskreter Produkte geeignete Kombinationen finden und dem Nutzer eine Entscheidungsgrundlage liefern.

Die Lösung soll dabei nicht nur auf eine einzelne Konfiguration beschränkt sein, sondern optional auch mehrere gute Alternativen bereitstellen, um verschiedene Kompromisse zwischen Preis und Protein darzustellen.

---

## 1.2 Kriterien zur Bewertung von Lösungen

Die Bewertung einer Lösung erfolgt primär anhand der Gesamtproteinmenge der ausgewählten Produkte. Diese stellt das Hauptoptimierungskriterium dar und bestimmt die Güte einer Lösung.

Zusätzlich können sekundäre Kriterien berücksichtigt werden, die jedoch eine untergeordnete Rolle spielen:
- Gesamtpreis (Einhaltung des Budgets als harte Grenze)
- Kalorienmenge (optional minimieren)
- Produktvielfalt (optional maximieren oder begrenzen)

Die wichtigste Bewertungsgröße bleibt jedoch eindeutig das Protein.

---

## 1.3 Erste Optimierungsfunktion und Optimierungsrichtung

Die grundlegende Optimierungsfunktion ist gegeben durch die Maximierung der Gesamtproteinmenge:

$$
f(x) = \sum_{i=1}^{n} Protein_i \cdot x_i
$$


Die Optimierungsrichtung ist damit eine **Maximierung**, da höhere Proteinwerte eine bessere Lösung darstellen.

Optional kann die Funktion durch einen Strafterm erweitert werden, um Budgetüberschreitungen zu berücksichtigen:

$$
f(x) = Protein(x) - \alpha \cdot \max(0, Preis(x) - Budget)
$$

---

## 1.4 Mehrkriterielle Bewertung und Ergebnisform

Falls mehrere Kriterien berücksichtigt werden, muss eine klare Priorisierung definiert werden. Die Priorität ist typischerweise wie folgt:

1. Einhaltung des Budgets (harte Nebenbedingung)
2. Maximierung des Proteins (Hauptziel)
3. Optimierung sekundärer Kriterien (z. B. Kalorien, Vielfalt)


## 1.5 Häufigkeit der Ausführung

Der Algorithmus wird typischerweise:
- **einmal pro Nutzeranfrage** ausgeführt (z. B. bei Eingabe eines Budgets)
- dabei wird direkt eine Lösung oder eine kleine Menge guter Lösungen zurückgegeben, so kann sich der Nutzer auch für eine passende Lösung mit Produkten die ihm besser gefallen entscheiden

Für Analyse- und Testzwecke kann der Algorithmus zusätzlich mehrfach ausgeführt werden (z. B. 20–30 Runs), um die Stabilität der Ergebnisse zu bewerten.

---

## 1.6 Qualitätserwartungen

Es wird erwartet, dass der Algorithmus:
- Lösungen mit hoher Proteinmenge findet
- das Budget möglichst effizient ausnutzt
- stabile Ergebnisse über mehrere Durchläufe liefert
- möglichst nahe am globalen Optimum arbeitet (keine exakte Garantie erforderlich)

---

## 1.7 Zeit- und Speicherbeschränkungen

Der Algorithmus muss so gestaltet sein, dass er im interaktiven Einsatz schnell reagiert. Das bedeutet:
- kurze Berechnungszeit pro Anfrage (nahe Echtzeit)
- keine hohen Speicheranforderungen
- effiziente Verarbeitung auch bei größeren Produktmengen

Für experimentelle Auswertungen sind längere Laufzeiten zulässig.

---

## 1.8 Zeitpunkt der Ergebnisbereitstellung

Die Ergebnisse werden unmittelbar nach der Berechnung benötigt. Das System soll also direkt nach der Anfrage eine Lösung oder mehrere gute Lösungen liefern, ohne zusätzliche Verzögerung oder Nachverarbeitung.

Für experimentelle Szenarien erfolgt die Ergebnisanalyse im Anschluss an mehrere unabhängige Läufe.