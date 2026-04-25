# Darstellungvariante Binär

## Ausgangslage

In Optimierungsproblemen wie Warenkorb-, Ernährungs- oder Budgetoptimierung ist eine binäre Vektordarstellung (0/1-Encoding) eine häufig verwendete Methode. Es kann ein **Produktvektor** verwendet werden.
Jeder Eintrag im Vektor steht dabei für ein Produkt aus der Datenbank.

$$
P = \{p_1, p_2, ..., p_n\}
$$

Eine Lösung ist ein Vektor:

$$
\mathbf{v} = (v_1, v_2, ..., v_k)
$$


Dabei wird jedes Produkt als binäre Entscheidungsvariable modelliert:

$$
x_i \in \{0,1\}
$$

- \(x_i = 1\) → Produkt ist im Warenkorb enthalten  
- \(x_i = 0\) → Produkt ist nicht enthalten  

Diese Darstellung ist mathematisch elegant und wird häufig in klassischen Knapsack- oder Set-Selection-Problemen verwendet.


---

### Entscheidung gegen die binäre Darstellung

Trotz ihrer theoretischen Vorteile haben wir uns in diesem Projekt bewusst gegen die binäre Repräsentation entschieden.

Der Hauptgrund dafür ist, dass unser Problem nicht nur eine reine Auswahlfrage ist, sondern zusätzlich **Mengen- und Konsumstruktur** abbilden muss.

---

### 1. Problem: Realistische Abbildung von Konsumverhalten

In der Praxis werden Produkte nicht nur *einmal gewählt oder nicht gewählt*, sondern in **mehreren Einheiten konsumiert**.

Beispiel:

- Müsli wird mehrfach gekauft
- Joghurt wird in Packungen konsumiert
- Proteinquellen werden in unterschiedlichen Mengen genutzt

Die binäre Darstellung:

$$
x_i \in \{0,1\}
$$

würde diese Realität stark vereinfachen und verzerren.

---

### 2. Verlust von Mengeninformation

Mit binärem Encoding geht folgende Information verloren:

- Wie oft ein Produkt gewählt wurde
- Wie stark ein Produkt in der Lösung vertreten ist
- Wie sich Konsumverhältnisse entwickeln

Beispiel:

| Darstellung | Interpretation |
|------------|----------------|
| `[1, 0, 1]` | Produkt A und C einmal enthalten |
| `[2, 0, 1]` | Produkt A doppelt, C einmal enthalten |

Die binäre Darstellung kann diese Unterschiede nicht abbilden:

$$
[1, 0, 1] \equiv [1, 0, 1]
$$

---

### 3. Einschränkungen bei der Fitness-Berechnung

Unsere Fitness-Funktion basiert stark auf aggregierten Werten:

- Proteinmenge
- Kalorien
- Portionsanzahl
- Geschmack (gewichtet)
- Vielfalt

Diese Größen sind **mengenabhängig**, nicht nur binär definierbar.

Eine binäre Darstellung würde künstlich voraussetzen, dass jedes Produkt nur eine fixe Wirkung hat – unabhängig von der Menge.

---

### 4. Einschränkungen für Optimierungsverhalten

Binäre Vektoren führen oft zu:

- zu grober Suche im Lösungsraum
- schlechter Anpassung an Budget- und Kalorienziele
- fehlender Feinsteuerung der Lösung

Unser Problem benötigt jedoch eine **kontinuierlichere Optimierung**, bei der Mengen schrittweise angepasst werden können.

---