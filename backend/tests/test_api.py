"""API, ingesta (F2), alertas (F7), PVT (F3), check-in (F4), reportes (F10) y persistencia."""
import importlib

from basal import db


def test_health_and_mission(fresh):
    assert fresh.get("/api/health").json()["ok"]
    m = fresh.get("/api/mission").json()
    assert m["dia"] == 38 and m["dias"] == 120
    assert m["parametros"]["red"] > m["parametros"]["yellow"]


def test_crew_has_profiles_and_six_indicators(fresh):
    crew = fresh.get("/api/crew").json()["tripulacion"]
    assert len(crew) >= 3
    assert all(len(a["indicadores"]) == 6 for a in crew)


def test_csv_import_validation(fresh):
    csv = ("astro_id,day,indicator,value,unit,source\n"
           "A1,10,rhr,61,bpm,csv\n"        # duplicado con la base -> rechazado sin sobrescribir
           "A1,10,rhr,62,lpm,csv\n"        # duplicado en el lote
           "A1,11,sleep,25,h,csv\n"        # imposible
           "A1,12,hrv,40,lpm,csv\n"        # unidad equivocada
           "ZZ,12,hrv,40,ms,csv\n"         # astronauta desconocido
           "A1,13,mood,,/10,csv\n"         # ausente
           "A1,500,mood,5,/10,csv\n")      # fuera de misión
    r = fresh.post("/api/ingest/csv", json={"csv": csv}).json()
    assert r["insertados"] == 0
    assert len(r["rechazados"]) == 7
    r2 = fresh.post("/api/ingest/csv", json={"csv": "astro_id,day,indicator,value,unit\nA1,10,rhr,61,lpm",
                                            "sobrescribir": True}).json()
    assert r2["reemplazados"] == 1
    bad = fresh.post("/api/ingest/csv", json={"csv": "a,b\n1,2"})
    assert bad.status_code == 422


def test_manual_measurement_and_impossible_value(fresh):
    ok = fresh.post("/api/measurements", json={"astro_id": "A2", "indicator": "rhr", "value": 64, "unit": "lpm"})
    assert ok.status_code == 200
    bad = fresh.post("/api/measurements", json={"astro_id": "A2", "indicator": "rhr", "value": 400})
    assert bad.status_code == 422


def test_alerts_are_explainable_and_reviewable(fresh):
    fresh.post("/api/mission/day", json={"day": 54})
    a = fresh.get("/api/astronauts/A1").json()
    assert a["alertas"], "La fatiga simulada de A1 debe generar alerta el día 54"
    al = a["alertas"][0]
    for f in ("id", "astro_id", "day", "nivel", "que_cambio", "cuanto", "como", "acciones", "evidencia", "estado"):
        assert f in al
    c = al["cuanto"][0]
    assert c["linea_base"] is not None and c["z"] is not None
    if al["nivel"] == "rojo":
        assert any("oficial médico" in x for x in al["acciones"])
    r = fresh.patch(f"/api/alerts/{al['id']}", json={"estado": "revisada", "nota": "Descanso extra"}).json()
    assert r["estado"] == "revisada"
    again = fresh.get("/api/astronauts/A1").json()["alertas"]
    assert any(x["id"] == al["id"] and x["estado"] == "revisada" for x in again)


def test_checkin_and_pvt(fresh):
    r = fresh.post("/api/astronauts/A1/checkin", json={"animo": 4, "calidad_sueno": 2}).json()
    assert r["reemplazados"] + r["insertados"] == 1
    p = fresh.post("/api/astronauts/A1/pvt", json={"modo": "pvtb_3min", "duracion_s": 180,
                                                  "rts": [250, 260, 400, 90, 300, 310, 280],
                                                  "anticipaciones": 1, "sin_respuesta": 1}).json()
    # lapsos: 400 + sin respuesta = 2; anticipaciones: 1 + respuesta de 90 ms = 2
    assert p["lapsos"] == 2 and p["anticipaciones"] == 2 and p["errores"] == 4 and p["valido"]
    inv = fresh.post("/api/astronauts/A1/pvt", json={"modo": "pvtb_3min", "duracion_s": 180,
                                                    "rts": [250] * 10, "interrupciones": 1}).json()
    assert not inv["valido"] and not inv["guardado_en_indicador"]


def test_reports_queue_respects_blackout(fresh):
    fresh.post("/api/mission/day", json={"day": 98})  # dentro del apagón 95–104
    rep = fresh.post("/api/reports", json={"desde": 0, "hasta": 98}).json()
    assert rep["estado"] == "pendiente"
    assert len(rep["contenido"]["tripulantes"]) == 4
    t = fresh.post("/api/reports/transmit").json()
    assert t["enviados"] == 0 and t["en_cola"] >= 1
    fresh.post("/api/mission/day", json={"day": 106})
    t2 = fresh.post("/api/reports/transmit").json()
    assert t2["enviados"] >= 1
    assert fresh.get(f"/api/reports/{rep['id']}").json()["estado"].startswith("enviado")
    csv = fresh.get(f"/api/reports/{rep['id']}/csv")
    assert csv.status_code == 200 and "indicador" in csv.text


def test_radiation_cumulative_separate_from_rate(fresh):
    fresh.post("/api/mission/day", json={"day": 90})
    r = fresh.get("/api/astronauts/A1").json()["radiacion"]
    assert r["acumulada_medida_mgy"] > r["presupuesto_escenario_mgy"] * 0.8
    assert "No es un límite" in r["supuesto"]


def test_create_astronaut_and_scenario(fresh):
    r = fresh.post("/api/astronauts", json={"id": "T9", "nombre": "Prueba", "rol": "Test"})
    assert r.status_code == 201 and r.json()["nivel"] in ("sin_dato", "calibrando")
    assert fresh.post("/api/astronauts", json={"id": "T9", "nombre": "Prueba", "rol": "Test"}).status_code == 409
    s = fresh.post("/api/sim/astronaut", json={"astro_id": "T9", "plan": [{"escenario": "C", "inicio": 40}]}).json()
    assert any(e["escenario"] == "C" for e in s["eventos"])


def test_persistence_after_restart(fresh):
    fresh.post("/api/mission/day", json={"day": 77})
    fresh.post("/api/astronauts/A3/checkin", json={"animo": 6, "calidad_sueno": 3, "notas": "persistencia"})
    # "Reiniciar": se recarga el módulo de servicios, que vuelve a leer SQLite
    from basal import services
    importlib.reload(services)
    services.init_db()
    assert db.get_mission()["current_day"] == 77
    assert db.one("SELECT notas FROM checkins WHERE astro_id='A3' ORDER BY id DESC")["notas"] == "persistencia"


def test_validation_endpoints(client):
    v = client.post("/api/validation/run", json={"n_misiones": 2, "semilla_inicial": 4000}).json()
    assert v["semillas"] == [4000, 4001] and "global" in v["resultados"]
    d = client.get("/api/validation/demo").json()
    assert "A1" in d["por_astronauta"]


def test_acknowledge_episode_and_snooze(fresh):
    fresh.post("/api/mission/day", json={"day": 72})
    al = fresh.get("/api/astronauts/A3").json()["alertas"]
    red = next(a for a in al if a["nivel"] == "rojo")
    r = fresh.patch(f"/api/alerts/{red['id']}", json={"estado": "reconocida", "revisor": "Oficial médica"}).json()
    assert r["estado"] == "reconocida" and r["revisor"] == "Oficial médica" and r["revisado_dia"] == 72
    # Todo el episodio anterior queda reconocido, no solo el día de hoy
    hist = fresh.get("/api/alerts?astro_id=A3").json()
    same = [a for a in hist if a["episodio"] == red["episodio"] and a["nivel"] == "rojo" and a["day"] <= 72]
    assert same and all(a["estado"] == "reconocida" for a in same)
    # El día siguiente, la alerta del mismo episodio hereda el reconocimiento
    fresh.post("/api/mission/day", json={"day": 73})
    nxt = [a for a in fresh.get("/api/alerts?astro_id=A3").json() if a["day"] == 73 and a["episodio"] == red["episodio"] and a["nivel"] == "rojo"]
    assert all(a["estado"] == "reconocida" and a["heredada"] for a in nxt)
    # Posponer (misión limpia): vuelve a pendiente al pasar el día
    fresh.post("/api/sim/reset", json={"seed": 7})
    fresh.post("/api/mission/day", json={"day": 72})
    fresh.patch(f"/api/alerts/{red['id']}", json={"estado": "pospuesta"})
    assert fresh.get("/api/alerts?astro_id=A3&estado=pospuesta").json()
    fresh.post("/api/mission/day", json={"day": 73})
    back = [a for a in fresh.get("/api/alerts?astro_id=A3").json() if a["id"] == red["id"]]
    assert back[0]["estado"] == "pendiente"
