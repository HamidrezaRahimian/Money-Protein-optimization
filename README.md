# Geld-zu-Protein-Optimierung

## Projektüberblick
Dieses Projekt entsteht im Rahmen des Moduls **Evolutionary Computing** an der DHBW Mosbach. Ziel ist die Entwicklung eines Optimierungsmodells, das aus einer begrenzten Auswahl von **LIDL-Produkten** einen möglichst proteinreichen Einkaufskorb zusammenstellt.

Der Fokus liegt klar auf **maximalem Protein**. Weitere Faktoren wie **Kosten**, **Kalorien**, **Geschmack**, **Abwechslung** und **Anzahl an Portionen** werden als **side variables** berücksichtigt.

> Kurz gesagt: Wir suchen mit Optimierungsverfahren die beste proteinorientierte Einkaufslösung bei einem festen Budget von **50 €**.

---

## Problemstellung
Viele proteinreiche Lebensmittel sind vergleichsweise teuer oder liefern nur in bestimmten Kombinationen einen guten Alltagsnutzen. Deshalb reicht ein einfacher Blick auf `protein per euro` allein nicht aus.

Dieses Projekt betrachtet das Problem realistischer:
- Wie kann man mit **50 € Budget** möglichst viel Protein einkaufen?
- Welche Kombination aus Produkten ist **praktisch**, **abwechslungsreich** und **sinnvoll portionierbar**?
- Wie lassen sich diese Anforderungen mit **Genetic Algorithms** und passenden **Baselines** optimieren?

---

## Ziel des Projekts
### Hauptziel
- **Maximierung der gesamten Proteinmenge** innerhalb eines festen Budgets

### Nebenziele
- möglichst gute **Kosten-Effizienz**
- sinnvolle **Kalorienwerte**
- gute **Taste / Präferenz**
- ausreichend **Variety**, damit nicht immer dieselben Produkte gewählt werden
- möglichst viele **Portionen / Meals** aus den gekauften Produkten

---

## Rahmenbedingungen
Für das Projekt gelten aktuell folgende feste Annahmen:

- **Store:** ausschließlich `LIDL`
- **Budget:** `50 €`
- **Datensatzgröße:** ca. `30 Produkte`
- **Packungsgröße pro Item:** maximal `500 g`
- einzelne Produkte können für **mehrere Portionen** verwendet werden
  - Beispiel: `300 g Rinderhack -> 2 Portionen`
- der Fokus liegt auf **Protein**, alle anderen Kriterien sind unterstützend

---

## Datensatz / Produktdatenbank
Als Datengrundlage wird eine einfache Produktdatenbank verwendet, voraussichtlich als `CSV`.

### Geplante Attribute pro Produkt
- `id`
- `name`
- `category`
- `price_eur`
- `weight_g`
- `protein_per_100g`
- `calories_per_100g`
- `taste_score`
- `portions`
- `protein_type` (`animal` / `plant` / `mixed`)
- `max_units`

### Beispielhafte Produktkategorien
- Skyr / Quark / Hüttenkäse
- Eier
- Hähnchen / Rind / Thunfisch
- Tofu / Linsen / Bohnen
- Haferflocken / Reis / Wraps
- Tiefkühlgemüse oder proteinfreundliche Beilagen

---

## Optimierungsidee
Das Problem wird als **kombinatorisches Optimierungsproblem** modelliert. Eine Lösung besteht aus einer Auswahl von Produkten und deren Mengen.

### Fitness Function
Die **Fitness Function** soll Protein am stärksten gewichten und andere Kriterien ergänzend einbeziehen.

Beispielhaft:

```text
fitness =
    hoher_Faktor * protein
  + kleiner_Faktor * portionen
  + kleiner_Faktor * geschmack
  + kleiner_Faktor * variety
  - penalty_fuer_budget
  - penalty_fuer_unpassende_kalorien
```

### Wichtige Logik
- **Protein** ist die wichtigste Zielgröße
- Budgetüberschreitung wird bestraft oder ausgeschlossen
- zu einseitige Lösungen sollen schlechter bewertet werden
- realistische Portionen und Mengen sollen bevorzugt werden

---

## Geplanter methodischer Ansatz
Im Projekt sollen mehrere Optimierungsansätze verglichen werden.

### Baselines
1. **Naive Baseline**
   - z. B. greedy Auswahl nach `protein-per-euro`
2. **Local Search Baseline**
   - Start mit einer gültigen Lösung, danach schrittweise Verbesserung

### Genetic Algorithms
Zusätzlich sollen mehrere Repräsentationen für den **Genetic Algorithm** entworfen werden.

Geplante Beispiele:
1. **Binary Representation**
   - Produkt wird gewählt oder nicht gewählt
2. **Integer Quantity Representation**
   - Produkt kann mit einer bestimmten Menge / Anzahl gewählt werden
3. **Meal-based Representation**
   - Fokus auf vordefinierte Portions- oder Meal-Kombinationen

Mindestens **zwei** dieser Ansätze werden implementiert und parametrisiert.

---

## Evaluationskriterien
Für den Vergleich der Ansätze sollen geeignete Metriken verwendet werden, zum Beispiel:

- Gesamtprotein
- Protein pro Euro
- Gesamtkosten
- Kalorienwert
- Anzahl der Portionen
- Variety Score
- Laufzeit
- Fitness-Verlauf über Generationen

Geplante Darstellungen:
- `Fitness over generations`
- Vergleich der finalen Lösungen
- Laufzeit- und Qualitätsvergleich zwischen den Ansätzen

---

## Motivation für die Modellierung
Der Mehrwert des Projekts liegt darin, dass nicht nur ein triviales Maximum gesucht wird, sondern eine **alltagstaugliche und nachvollziehbare Lösung**.

Das bedeutet konkret:
- nicht nur das billigste Proteinprodukt kaufen
- nicht 10-mal dasselbe Lebensmittel wählen
- Portionen realistisch berücksichtigen
- geschmackliche und praktische Aspekte mitdenken

So entsteht ein Optimierungsproblem, das sowohl technisch interessant als auch realitätsnah ist.

---

## Projektstatus
Aktueller Stand: **Konzeptions- und Planungsphase**

Die nächsten Schritte sind:
1. Datensatz mit ca. 30 LIDL-Produkten erstellen
2. Fitness Function formal definieren
3. Repräsentationsalternativen entwerfen
4. Baselines und Genetic Algorithms implementieren
5. Ergebnisse vergleichen und dokumentieren

---

## Team & Zusammenarbeit
Dieses Projekt wird in einer **3er-Gruppe** umgesetzt. Code, Dokumentation und Zusammenarbeit werden transparent über GitLab verwaltet.

Geplant ist eine klare Aufteilung in:
- Anforderungsanalyse und Problemdefinition
- Implementierung der Optimierungsverfahren
- Evaluation, Vergleich und Dokumentation

---

## Hinweis
Dieses README beschreibt die aktuelle Projektidee und wird im Verlauf der Bearbeitung weiter konkretisiert und erweitert.
