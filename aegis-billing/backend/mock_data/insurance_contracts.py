"""
Mockovani ugovori osiguravajucih kuca.
U produkciji, ovi PDF-ovi se ucitavaju u Graph RAG (Vertex AI Search / Neptune).
Za demo, predstavljamo ih kao tekst koji se daje Agent 2 (Contract Lawyer).
"""

GLOBAL_HEALTH_CONTRACT = """
GLOBAL HEALTH INSURANCE - UGOVOR O ZDRAVSTVENOM POKRICU
Verzija 2026.1 | Vazi od: 01.01.2026

CLAN 4.2 - DIJAGNOSTICKE PROCEDURE
4.2.1 Ultrazvucne procedure (CPT 76700-76770):
  - Pokrivene su uz dokumentovanu klinicku indikaciju
  - Obavezna je najmanje JEDNA ICD-10 sifra koja opravdava indikaciju
  - Prihvatljive kategorije: R10.x (abdominalni bol), R19.x (digestivni simptomi),
    K00-K93 (bolesti digestivnog sistema), N00-N99 (bolesti urogenitalnog trakta)

4.2.2 MRI procedure (CPT 70551-70553 - MRI mozga):
  - Ogranicenje: maksimalno JEDAN MRI mozga u periodu od 6 meseci po pacijentu
  - IZUZETAK: ne primenjuje se ako postoji ICD-10 sifra iz kategorije I60-I69
    (cerebrovaskularne bolesti, ukljucujuci infarkt mozga)
  - Obavezna je dijagnoza iz kategorija G00-G99 (bolesti nervnog sistema)
    ili R51 (glavobolja) ili S06.x (intrakranijalna povreda)

4.2.3 Rutinski godisnji pregled (CPT 99396, 99397):
  - Pokriven jednom godisnje za odrasle pacijente
  - Ne zahteva specificne ICD-10 sifre dijagnoze
  - Prihvatljiva je Z00.00 (opsti medicinski pregled bez tegoba)

CLAN 5.1 - LABORATORIJSKI TESTOVI
5.1.1 Kompletna krvna slika (CPT 85025):
  - Pokrivena uz rutinski pregled ili konkretan klinicki razlog
  - Pri sumnji na anemiju, infekciju ili maligne procese - obavezne D50-D89 ili B95-B97

CLAN 7 - GENERICKI USLOVI
7.1 Sve dijagnosticke procedure moraju biti potkrepljene najmanje jednom
    dijagnostickom ICD-10 sifrom koja je medicinski povezana sa procedurom.
7.2 Procedure bez klinicke indikacije se automatski odbijaju.
"""

INSURANCE_CONTRACTS = {
    "Global Health Insurance": GLOBAL_HEALTH_CONTRACT,
}


def get_contract(insurance_company: str) -> str:
    return INSURANCE_CONTRACTS.get(
        insurance_company,
        "Generican ugovor: sve procedure moraju imati ICD-10 opravdanje."
    )
