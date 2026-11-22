# ha-config

Home Assistant-configuratie voor thuis: energie (P1, PV, batterij, capaciteitstarief, dynamische prijzen),
verwarming (Vaillant + Austroflamm-pelletkachel), huishouden, gezin en een kiosk-dashboard voor een 7"-touchscreen.

Alles staat in **packages** (één bestand per domein). Externe entiteiten zijn placeholders die je na installatie
in één keer koppelt met `tools/koppel_entiteiten.py`.

```
configuration.yaml        hoofdconfig, laadt packages/ en het kiosk-dashboard
entiteiten.yaml           placeholder -> echte entity_id
packages/
  energie.yaml            P1, PV, Marstek, voorspelde kwartierpiek, peak shaving, batterijscripts
  prijzen.yaml            ENTSO-E, goedkoop uur, PV-verwachting, batterij laden van net, negatieve prijs
  verwarming.yaml         Vaillant <-> kachel, pelletvoorraad, storingsmelding
  huishouden.yaml         wasmachine/droogkast klaar, afvalophaling
  gezin.yaml              Smartschool, NMBS-vertraging
  promoties.yaml          Lidl (trefwoorden) + Colruyt (watchlist via REST), melding bij nieuwe promo
  nieuws.yaml             VRT NWS -> koppen (optioneel AI-samenvatting) -> voorlezen met Piper
  onderhoud.yaml          Watchman, temperatuur en schijf van de Pi
dashboards/kiosk.yaml     3 views: Energie / Vandaag / Info
tools/koppel_entiteiten.py
```

De configuratie is gevalideerd met `hass --script check_config` (Home Assistant 2026.2) en een korte opstarttest.

---

## 1. Installatie Raspberry Pi 5

- [ ] Pi 5 (4 of 8 GB) + officiële 27 W-voeding + **M.2 HAT+ met NVMe-SSD** (geen SD-kaart voor de recorder)
- [ ] Bootloader updaten zodat de Pi van NVMe opstart (Raspberry Pi Imager > Misc utility images > Bootloader > NVMe/USB Boot)
- [ ] **Home Assistant OS** voor Pi 5 op de SSD zetten met Raspberry Pi Imager
- [ ] Bekabeld netwerk, vast IP-adres via DHCP-reservatie in de router
- [ ] Onboarding: locatie Kortrijk, eenheden metrisch, tijdzone Europe/Brussels
- [ ] Add-ons: **File editor** of **Studio Code Server**, **Terminal & SSH**, **Mosquitto broker**
- [ ] Automatische back-ups instellen (Instellingen > Systeem > Back-ups), met een externe locatie (NAS)
- [ ] **HACS** installeren (hacs.xyz)

## 2. Integraties (in deze volgorde)

| Domein | Integratie | Bron | Opmerking |
|---|---|---|---|
| Meldingen | Companion app op je gsm | officieel | levert `notify.mobile_app_...` en aanwezigheid |
| Energie | **HomeWizard** | officieel | lokale API aanzetten in de HomeWizard-app |
| Energie | **Shelly** | officieel | wordt automatisch ontdekt |
| Energie | **SolarEdge Modbus Multi** | HACS | eerst Modbus TCP aanzetten via SetApp (poort 1502) |
| Energie | **Marstek Venus Modbus** of **Marstek Local API** | HACS | Modbus is volgens gebruikers stabieler |
| Prijzen | **ENTSO-E** | HACS | gratis API-token aanvragen bij ENTSO-E Transparency |
| PV-verwachting | **Forecast.Solar** | officieel | oriëntatie, helling en kWp van je panelen; Solcast (HACS) is nauwkeuriger |
| Nieuws (optioneel) | **Ollama** of **Google Gemini** | officieel | alleen voor een AI-samenvatting; zonder worden de koppen voorgelezen |
| Nieuws | **Piper** + **Wyoming** | add-on / officieel | lokale TTS, Vlaamse stem `nl_BE-nathalie-medium` |
| Onderhoud | **System Monitor** | officieel | sensoren CPU-temperatuur en schijfgebruik aanzetten |
| Onderhoud | **Watchman** | HACS | best als laatste installeren, na het koppelen van de entiteiten |
| Verwarming | **myVAILLANT** | HACS | cloud, login van de myVAILLANT-app |
| Verwarming | **Austroflamm** (Fumis) | officieel | vereist Fumis WiRCU-wifimodule |
| Weer | **Buienradar** | officieel | levert ook `camera.buienradar` |
| Weer | **IRM KMI** | HACS | Belgische voorspelling, waarschuwingen, radar |
| Mobiliteit | **NMBS** | officieel | traject instellen, bv. Kortrijk -> Gent-Sint-Pieters |
| Gezin | **Remote Calendar** | officieel | iCal-link uit Smartschool (Schoolkalender > Exporteren) |
| Promoties | **Lidl Weekly Offers** | HACS | Lidl Plus-login, trefwoordfilters (koffie, luiers, ...) |
| Promoties | Colruyt | ingebouwd (RESTful) | geen installatie; winkel-id en product-id's instellen, zie `promoties.yaml` |
| Afval | **Recycle!** of iCal | HACS / officieel | moet een `calendar`-entiteit opleveren |
| Beurs | **Yahoo Finance** | HACS | tickers bv. `^BFX`, `IWDA.AS` |

HACS-frontendkaarten: **power-flow-card-plus**, **clock-weather-card**, **mini-graph-card**, **kiosk-mode**.

## 3. Deze config plaatsen

1. Kopieer `configuration.yaml`, `packages/`, `dashboards/`, `tools/` en `entiteiten.yaml` naar `/config`.
   Heb je al een `configuration.yaml`, voeg dan alleen het `homeassistant: packages:`-blok en het
   `lovelace:`-blok toe.
2. Vul `entiteiten.yaml` aan. Rechts komt de echte entity_id (Ontwikkelhulpmiddelen > Statussen).
3. In de Terminal-add-on:
   ```bash
   cd /config
   python3 tools/koppel_entiteiten.py --check     # overzicht
   python3 tools/koppel_entiteiten.py             # vervangen
   python3 tools/koppel_entiteiten.py --verify http://localhost:8123 <LONG_LIVED_TOKEN>
   ```
4. Ontwikkelhulpmiddelen > YAML > **Configuratie controleren**, daarna herstarten.
5. Zet de schakelaars aan die je wilt gebruiken (ze staan standaard **uit**):
   - `input_boolean.peak_shaving_actief`
   - `input_boolean.laden_op_goedkope_uren`
   - `input_boolean.kachel_vaillant_koppeling`

Tip: zet `/config` onder git (Studio Code Server heeft git ingebouwd) en push naar deze repo.
`secrets.yaml` en `.storage/` staan in `.gitignore`.

## 4. Na het koppelen controleren

- **P1:** `p1_vermogen` moet positief zijn bij afname en negatief bij injectie. `p1_kwartiergemiddelde` is
  het gemiddelde van het **lopende** kwartier in W. Als HomeWizard kW gebruikt, pas dan de templates aan.
- **Batterij:** `batterij_vermogen` is positief bij **ontladen**. Is het bij jou omgekeerd, zet dan
  `batterij_teken` op `-1` in `energie.yaml`.
- **Marstek-sturing:** de 3 scripts onderaan `energie.yaml` zijn de enige plek met Marstek-specifieke
  entiteiten. Controleer de optienamen van de select (`discharge` / `charge` / `none`) en test elk script
  met de hand voordat je peak shaving aanzet.
- **myVAILLANT:** een temperatuurwijziging zet standaard een quick veto. De automatisatie bewaart het
  oude setpoint en zet het terug.
- **Pellets:** stel `Branduren per volle tank` in na één of twee vullingen. Druk op *Pellets bijgevuld*
  telkens je de kachel vult.
- **NMBS:** de melding gebruikt de attributen `delay_minutes`, `canceled` en `platform_departing` en werkt
  op weekdagen tussen 06:00 en 09:00.

## 5. Kiosk-scherm

**Optie A: scherm aan dezelfde Pi.** Add-on **HAOS-kiosk** (repository `puterboy/HAOS-kiosk`).
Zet als URL `http://localhost:8123/dashboard-kiosk/vandaag` en gebruik een aparte HA-gebruiker voor de kiosk.

**Optie B: aparte Pi aan de muur.** Raspberry Pi OS + **TouchKio** (`leukipp/touchkio`). Dezelfde URL, maar
met het IP-adres van de HA-server.

Het dashboard verbergt de kop- en zijbalk via kiosk-mode. Voeg `?disable_km` toe aan de URL om ze tijdelijk
terug te zien.

## Colruyt-watchlist

1. Test eerst of het endpoint vanaf je netwerk werkt (Terminal-add-on):
   `curl -s "https://ecgproductmw.colruyt.be/ecgproductmw/v2/nl/products/369?clientCode=clp&placeId=620" | head -c 400`
2. Winkel-id: kies je winkel op colruyt.be, F12 > Netwerk, filter op `ecgproductmw` en neem het getal na `placeId=`.
   Vul het in bij *Colruyt winkel-id* (Info-view van het dashboard).
3. Product-id: open het product, dezelfde netwerkfilter, het getal na `/products/`.
4. Per product één `rest:`-blok kopiëren in `promoties.yaml` (voorbeeld en sjabloon staan erin) en de configuratie herladen.

Nieuwe producten verschijnen vanzelf in *Colruyt in promo* en in de meldingen.

## Hoe de peak shaving werkt

```
voorspelde kwartierpiek = (gemiddelde_tot_nu * t + vermogen_nu * (900 - t)) / 900
effectieve grens        = max(ingestelde drempel, maandpiek)
piek dreigt             = voorspelling > grens * marge%      -> batterij ontladen
piek voorbij (2 min)    -> batterij terug naar automatisch (alleen als peak shaving hem had overgenomen)
```

Laden van het net op goedkope uren gebeurt nooit terwijl er een piek dreigt, en ook niet als de zon
de batterij straks toch vult: vóór 14u telt de resterende PV-verwachting van vandaag, daarna die van morgen
(drempel instelbaar, standaard 8 kWh). Bij een negatieve stroomprijs wordt er altijd geladen.
