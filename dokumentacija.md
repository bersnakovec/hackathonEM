# Dokumentacija aplikacije `EM_outage_tracker`

## Namen projekta

`EM_outage_tracker` je analitična aplikacija za pregled napetostnih meritev nizkonapetostnega omrežja. Uporabnik lahko naloži eno ali več CSV datotek z meritvami, aplikacija pa:

- prikaže napetostne grafe,
- zazna potencialne anomalije z uporabo že treniranega modela XGBoost,
- loči daljše izpade od kratkih anomalnih meritev,
- izračuna kazalnika **SAIDI** in **SAIFI** za naložene podatke.

Aplikacija je namenjena prikazu in analizi podatkov iz terena ter hitremu pregledu možnih težav na merilnih mestih.

## Glavne funkcionalnosti

- nalaganje ene ali več `.csv` datotek hkrati,
- prikaz **skupnega grafa** za več datotek ali **ločene vizualizacije** po datoteki,
- dinamično zaznavanje anomalij z modelom `xgboost_anomaly_model.pkl`,
- označevanje kratkih anomalij z živahno barvo in daljših izpadov z drugo barvno oznako,
- izračun osnovnih zanesljivostnih kazalnikov omrežja,
- prikaz podatkov brez prikazanega leta na časovni osi.

## Zagon aplikacije

### 1. Namestitev odvisnosti

V terminalu zaženite:

```powershell
pip install -r requirements.txt
```

### 2. Zagon Streamlit aplikacije

```powershell
streamlit run app.py
```

Po zagonu se aplikacija odpre v brskalniku. V stranski vrstici naložite CSV datoteke za analizo.

## Potrebni vhodni podatki

Aplikacija pričakuje CSV datoteke s podatki v obliki, podobni primerom v mapi `data/ovrednoteni_podatki/`.

Pri nalaganju datoteke aplikacija pričakuje naslednja polja po stolpcih:

1. **ID** merilnega mesta,
2. **Timestamp** v formatu `dd.mm HH:MM`,
3. **Voltage** oziroma izmerjena napetost,
4. **Status** ali podoben indikator stanja.

Pomembno:

- aplikacija ne prikazuje leta na časovni osi grafov,
- notranje pa čas uporablja kot `datetime` za pravilno risanje in označevanje anomalij,
- pri neustreznih vrsticah se manjkajoče vrednosti odstranijo iz analize.

## Obdelava podatkov

V `app.py` aplikacija najprej prebere CSV datoteke, jih očisti in normalizira:

- `ID` se pretvori v število,
- `Timestamp` se pretvori v datum in čas,
- `Voltage` se pretvori v numerično vrednost,
- podatki brez ključnih vrednosti se odstranijo.

Nato aplikacija izvede pripravo značilk za model:

- zamiki `lag_1`, `lag_2`, `lag_3`,
- `rolling_mean`,
- `rolling_std`,
- `velocity`.

Te značilke so enake tistim, ki jih model pričakuje ob napovedovanju anomalij.

## Umetna inteligenca in zaznavanje anomalij

Aplikacija uporablja že naučen model iz datoteke `xgboost_anomaly_model.pkl` in seznam vhodnih značilk iz `model_features.pkl`.

Model se uporabi dinamično ob vsaki novi naloženi datoteki, zato aplikacija ne temelji več samo na predhodno pripravljenih napovedih. Tako lahko obdeluje tudi nove podatke, ki jih model prej še ni videl.

Logika vizualizacije loči med:

- **daljšimi izpadi**: dogodki, ki trajajo vsaj 3 ure,
- **kratkimi anomalijami**: krajši nenavadni odkloni napetosti.

Kratke anomalije so na grafu posebej poudarjene, da jih je mogoče hitro opaziti.

## Kazalniki SAIDI in SAIFI

V aplikaciji sta prikazana dva ključna kazalnika zanesljivosti omrežja:

- **SAIDI** – povprečno trajanje izpada na uporabnika,
- **SAIFI** – povprečno število prekinitev na uporabnika.

Izračun temelji na zaznanih daljših izpadih v naloženih podatkih.

### Pojasnilo izpisov na nadzorni plošči

- **col1**: skupno število merilnih točk,
- **col2**: SAIDI,
- **col3**: SAIFI.

## Vizualizacija grafov

Na voljo sta dva načina prikaza:

1. **Separate graph per file**
   - vsaka naložena datoteka se prikaže posebej,
   - primerna izbira za podrobno analizo posameznega merilnika ali datoteke.

2. **Combined graph**
   - več datotek je prikazanih na enem grafu,
   - primerna izbira za primerjavo med merilnimi mesti ali časovnimi serijami.

Na grafu se anomalije prikazujejo z barvnimi poudarki, daljši izpadi in krajše anomalije pa so ločeno označeni.

## Struktura projektnih datotek

- `app.py` – glavna Streamlit aplikacija,
- `train_model.py` – skripta za učenje modela,
- `xgboost_anomaly_model.pkl` – shranjen treniran model,
- `model_features.pkl` – seznam značilk, ki jih model pričakuje,
- `requirements.txt` – seznam odvisnosti,
- `data/ovrednoteni_podatki/` – označeni podatki za učenje modela,
- `rezultati.csv` – izhodni ali analitični podatki projekta,
- `Hackathon_projekt.ipynb` – razvojni notebook s pripravo modela in analize.

## Učenje modela

Datoteka `train_model.py` vsebuje proces učenja modela:

- prebere označene podatke iz `data/ovrednoteni_podatki/`,
- izvede feature engineering,
- trenira klasifikator `XGBClassifier`,
- shrani model z uporabo `joblib`.

Če želite model ponovno naučiti, zaženite:

```powershell
python train_model.py
```

## Odvisnosti

Projekt uporablja naslednje glavne knjižnice:

- `streamlit` za uporabniški vmesnik,
- `pandas` za obdelavo podatkov,
- `plotly` za grafe,
- `numpy` za numerične izračune,
- `xgboost` za model anomalij,
- `scikit-learn` kot podpora pri strojnem učenju.

## Kratek povzetek za uporabo

1. Namestite odvisnosti.
2. Zaženite `streamlit run app.py`.
3. Naložite eno ali več CSV datotek.
4. Izberite način prikaza grafa.
5. Preglejte SAIDI, SAIFI in označene anomalije.




