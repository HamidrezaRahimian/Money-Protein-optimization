# 3. Risikobewertung

Die Anwendung eines genetischen Algorithmus auf dieses Optimierungsproblem ist grundsätzlich geeignet, birgt jedoch mehrere strukturelle und algorithmische Risiken, die insbesondere aus der hohen Komplexität des Suchraums sowie der Nebenbedingungen resultieren.

---

## 1. Suchraumkomplexität und Skalierungsprobleme

Ein zentrales Risiko ist die enorme Größe des Suchraums, wodurch das Problem einem klassischen „Nadel-im-Heuhaufen“-Szenario entspricht. Gute Lösungen sind selten und nicht gleichmäßig verteilt, was dazu führt, dass der Algorithmus unter Umständen sehr viele Generationen benötigt, um überhaupt in die Nähe hochwertiger Lösungen zu gelangen.

Die Schwierigkeit steigt zusätzlich stark mit der Instanzgröße. Während kleine Problemgrößen oft schnell lösbar sind, können größere Instanzen den Algorithmus erheblich verlangsamen oder in suboptimalen Bereichen stagnieren lassen. Obwohl die Fitnessberechnung selbst effizient ist, kann die Gesamtanzahl der benötigten Bewertungen zu einer kritischen Laufzeit führen.

---

## 2. Lokale Optima und Diversitätsprobleme

Ein weiteres wesentliches Risiko ist das Auftreten lokaler Optima. Aufgrund der Struktur des Problems existieren viele Lösungen, die lokal sehr gut erscheinen, global jedoch deutlich schlechter sind. Dies kann dazu führen, dass der Algorithmus frühzeitig in suboptimalen Bereichen feststeckt.

Dieses Problem wird insbesondere dann verstärkt, wenn die Populationsdiversität zu gering ist oder die Selektionsstrategie zu stark auf Exploitation ausgerichtet ist. In solchen Fällen verliert der Algorithmus seine Fähigkeit zur globalen Exploration.

---

## 3. Constraint- und Modellierungsrisiken

Ein kritischer Aspekt ist die korrekte Behandlung der Budget-Constraint. Wenn diese nicht strikt eingehalten oder nicht korrekt über eine Penalty-Funktion modelliert wird, kann es zu ungültigen oder unrealistischen Lösungen kommen.

Insbesondere die Skalierung der Fitnessfunktion spielt hier eine zentrale Rolle: Eine zu schwache Strafkomponente führt dazu, dass Budgetverletzungen toleriert werden, während eine zu starke Gewichtung valide Lösungen verdrängen kann.

Auch die Wahl der Repräsentation (binär vs. ganzzahlig) beeinflusst die Qualität der Suche erheblich und kann bei falscher Modellierung die Lösungsfähigkeit des Algorithmus einschränken.

---

## 4. Zielkonflikte und Bewertungsprobleme

Bei mehrkriteriellen Erweiterungen (z. B. Kombination aus Protein, Kalorien und Vielfalt) entsteht das Risiko widersprüchlicher Optimierungsziele. Ohne klare Priorisierung kann dies zu instabilen oder schwer interpretierbaren Ergebnissen führen.

Daher ist eine eindeutige Strukturierung erforderlich, entweder durch Priorisierung (harte Reihenfolge der Ziele) oder sauber gewichtete Fitnessfunktionen mit sinnvoller Skalierung

---

## 5. Stabilität und Ergebnisvarianz

Da genetische Algorithmen stochastisch arbeiten, besteht ein natürliches Risiko schwankender Ergebnisse zwischen einzelnen Läufen. Ohne ausreichende Wiederholungen kann dies zu verzerrten oder nicht repräsentativen Ergebnissen führen.

Daher ist es notwendig, mehrere unabhängige Durchläufe durchzuführen und die Ergebnisse statistisch auszuwerten, um robuste Aussagen über die Qualität des Algorithmus treffen zu können.


# Fazit

Insgesamt handelt es sich um ein klassisches NP-schweres Optimierungsproblem mit stark kombinatorischem Charakter. Aufgrund der großen Suchräume, der vielen lokalen Optima und der komplexen Nebenbedingungen ist der Einsatz eines genetischen Algorithmus besonders geeignet. Gleichzeitig erfordert das Problem eine sorgfältige Modellierung der Fitnessfunktion, der Repräsentation und der Constraint-Behandlung, um stabile und qualitativ hochwertige Ergebnisse zu erzielen.