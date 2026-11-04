"""
Inteligentna klimatyzacja z logiką rozmytą (Python, scikit-fuzzy)

Opis problemu:
     (killka zdań: co sterujemy, jakie są wejścia i wyjścia, po co logika rozmyta...)

Autorzy:
 - Alicja Chełminiak (s29093)
 - Marceli Gosztyła (s23319)

Przygotowanie środowiska:
     1. Zainstaluj Python 3.10+
     2. cd Zadanie_2
     3. pip install -r requirements.txt
     4. python klimatyzacja.py
"""

import argparse
import math
import os
from cmath import polar

import numpy as np
import skfuzzy as fuzz
from numpy.f2py import rules
from skfuzzy import control as ctrl

# Temperatura, do której dąży klimatyzacja (C)
TEMPERATURA_DOCELOWA = 24.0
# Temperatura w pokoju na początku symulacji (C)
TEMPERATURA_POCZATKOWA = 27.0
# Godzina rozpoczęcia symulacji
GODZINA_START = 8
# Długość symulacji w minutach (8:00 - 20:00)
LICZBA_MINUT = 720
# Ile minut symulacji przypada na jedną klatkę animacji
MINUT_NA_KLATKE = 3
# Liczba osób w pokoju: (od której minuty, ile osób)
HARMONOGRAM_OSOB = [(0, 2), (60, 8), (180, 15), (300, 6), (420, 16), (600, 4)]


def zbuduj_system():
    """Buduje sterownik rozmyty: zmienne, funkcje przynależności i reguły.

    Parametry:
    brak

    Zwraca:
    tuple: (symulator, zmienne), gdzie symulator to ControlSystemSimulation gotowy do obliczeń, a zmienne to słownik
    nazwa -> zmienna rozmyta (używany do rysowania funkcji przynależności)
    """

    # Zmienne wejściowe (Antecedent) - zakres wartości, jakie mogą przyjmować
    temperatura = ctrl.Antecedent(np.arange(10, 40.5, 0.5), "Temperatura")
    wilgotnosc = ctrl.Antecedent(np.arange(0, 101, 1), "Wilgotnosc")
    osoby = ctrl.Antecedent(np.arange(0, 21, 1), "Osoby")
    slonce = ctrl.Antecedent(np.arange(0, 101, 1), "Slonce")

    # Zmienne wyjściowe (Consequent), domyślne defuzyfikacja metodą centroidu
    moc = ctrl.Consequent(np.arange(0, 101, 1), "Moc")
    wentylator = ctrl.Consequent(np.arange(0, 101, 1), "Wentylator")

    # Funkcje przynależności (trapezowe na brzegach, trójkątne w środku).
    # Zbiory zachodzą na siebie, dzięki czemu sterowanie jest płynne.
    temperatura["niska"] = fuzz.trapmf(temperatura.universe, [10, 10, 18, 22])
    temperatura["komfortowa"] = fuzz.trimf(temperatura.universe, [20, 24, 28])
    temperatura["wysoka"] = fuzz.trapmf(temperatura.universe, [26, 30, 40, 40])

    wilgotnosc["niska"] = fuzz.trapmf(wilgotnosc.universe, [0, 0, 30, 50])
    wilgotnosc["srednia"] = fuzz.trimf(wilgotnosc.universe, [30, 50, 70])
    wilgotnosc["wysoka"] = fuzz.trapmf(wilgotnosc.universe, [50, 70, 100, 100])

    osoby["malo"] = fuzz.trapmf(osoby.universe, [0, 0, 2, 6])
    osoby["srednio"] = fuzz.trimf(osoby.universe, [3, 8, 13])
    osoby["duzo"] = fuzz.trapmf(osoby.universe, [10, 15, 20, 20, ])

    slonce["slabe"] = fuzz.trapmf(slonce.universe, [0, 0, 20, 45])
    slonce["srednie"] = fuzz.trimf(slonce.universe, [25, 50, 75])
    slonce["mocne"] = fuzz.trapmf(slonce.universe, [55, 80, 100, 100])

    for wyjscie in (moc, wentylator):
        wyjscie["mala"] = fuzz.trimf(wyjscie.universe, [0, 0, 40])
        wyjscie["srednia"] = fuzz.trimf(wyjscie.universe, [20, 50, 80])
        wyjscie["duza"] = fuzz.trimf(wyjscie.universe, [60, 100, 100])

    # Baza reguł JEZELI-TO. W regułach: & oznacza I (minimum), | oznacza LUB (maksimum).
    reguly = [
        # --- moc chłodzenia ---
        ctrl.Rule(temperatura["niska"], moc["mala"]),
        ctrl.Rule(temperatura["komfortowa"] & slonce["slabe"], moc["mala"]),
        ctrl.Rule(
            temperatura["komfortowa"]
            & (slonce["srednia"] | slonce["mocne"] | osoby["srednio"] | osoby["duzo"]),
            moc["srednia"],
        ),
        ctrl.Rule(temperatura["komfortowa"] & wilgotnosc["wysoka"], moc["srednia"]),
        ctrl.Rule(temperatura["wysoka"], moc["duza"]),
        ctrl.Rule(
            temperatura["wysoka"] & osoby["malo"] & slonce["slabe"], moc["srednia"]
        ),
        # --- prędkość wentylatora ---
        ctrl.Rule(temperatura["niska"], wentylator["mala"]),
        ctrl.Rule(temperatura["komfortowa"] & osoby["malo"], wentylator["mala"]),
        ctrl.Rule(temperatura["komfortowa"] & wilgotnosc["niska"], wentylator["mala"]),
        ctrl.Rule(
            temperatura["komfortowa"]
            & (osoby["srednio"] | osoby["duzo"] | wilgotnosc["wysoka"]),
            wentylator["srednia"],
        ),
        ctrl.Rule(temperatura["wysoka"], wentylator["duza"]),
        ctrl.Rule(temperatura["wysoka"] & osoby["malo"], wentylator["srednia"]),
    ]

    symulator = ctrl.ControlSystemSimulation(ctrl.ControlSystem(reguly))
    zmienne = {
        "temperatura": temperatura,
        "wilgotnosc": wilgotnosc,
        "osoby": osoby,
        "slonce": slonce,
        "moc": moc,
        "wentylator": wentylator,
    }
    return symulator, zmienne


def dblicz_sterowanie(symulator, temperatura, wilgotnosc, osoby, slonce):
    """Przelicza wejscia na wyjscia sterownika rozmytego.

    Parametry:
    symulator (ControlSystemSimulation): Sterownik z funkcji zbuduj_system
    temperatura (float): Temperatura w pokoju (C)
    wilgotnosc (float): wilgotnosc powietrza (%)
    osoby (float): liczba osob w pokoju
    slonce (float): naslonecznienie (%)

    Zwraca:
    tuple[float, float]: (moc chłodzenia w %, prędkość wentylatora w %)
    """
    # Wartosci spoza zakresu zmiennych rozmytych obcinamy do jego granic
    symulator.input["temperatura"] = float(np.clip(temperatura, 10, 40))
    symulator.input["wilgotnosc"] = float(np.clip(wilgotnosc, 0, 100))
    symulator.input["osoby"] = float(np.clip(osoby, 0, 20))
    symulator.input["slonce"] = float(np.clip(slonce, 0, 100))
    symulator.compute()
    return float(symulator.output["moc"]), float(symulator.output["wentylator"])


class Pokoj:
    """ Prosty model fizyczny pokoju (temperatura i wilgotność).

    Temperatura rośnie od ciepła z zewnątrz, od ludzi i od słońca,
    a maleje dzięki chłodzeniu klimatyzacji.
    """
    def __init__(self, temperatura=TEMPERATURA_POCZATKOWA, wilgotnosc=55.0):
        """Tworzy pokój w zadanym stanie początkowym.
        Parametry:
        Temperatura (float): Poczatkowa temperatura (C)
        wilgotnosc (float): Początkowa wilgotność (%)

        Zwraca:
        None
        """
        self.temperatura = temperatura
        self.wilgotnosc = wilgotnosc

    def krok(self, moc, wentylator, osoby, slonce, t_zewn):
        """Przesuwa stan pokoju o jedna minute.

        Parametry:
        moc (float): Moc chlodzenia (0-100 %)
        wentylator (float): predkosc wentylatora (0-100 %)
        osoby (float): liczba osob w pokoju
        slonce (float): naslonecznienie (0-100 %)
        t_zewn (float): Temperatura na zewnatrz (C)

        Zwraca:
        None
        """
        # Dopływ ciepła: przez ściany, od ludzi i od słońca (C na minytę
        przyrost = 0.004 * (t_zewn - self.temperatura) + 0.0008 * osoby + 0.0004 * slonce
        # Chłodzenie jest skuteczniejsze, gdy wentylator rozprowadza chłód
        chlodzenie = 0.15 * (moc / 100) * (0.6 + 0.4 * wentylator / 100)
        self.temperatura = float(np.clip(self.temperatura + przyrost - chlodzenie, 10, 40))

        # Wilgotność dąży do poziomu zależnego od liczby osób i chłodzenia
        cel = 40 + 1.5 * osoby - 0.15 * moc
        self.wilgotnosc = float(np.clip(self.wilgotnosc + 0.05 * (cel - self.wilgotnosc), 0, 100))

def scenariusz(minuta):
    """Zwraca warunki zewnętrzne w danej minucie symulacji.

    Parametry:
    minuta (int): Numer minuty od początku symulacji (0 = godzina startu)

    Zwraca:
    tuple[float, float, float]: (liczna osób, nasłonecznienie w %, temperatura na zewnątrz w C)
    """
    godzina = GODZINA_START + minuta / 60
    #Słońce wschodi o 6:00, w południe jest najsilniejsze, zachodzi o 20:00
    slonce = 100 * max(0.0, math.sin(math.pi * (godzina - 6) / 14))
    # Na zewnątrz najcieplej jest około 14:00
    t_zewn = 24 +10 * math.sin(math.pi * (godzina - 8) / 12)
    osoby = 0
    for od_minuty, liczba in HARMONOGRAM_OSOB:
        if minuta >= od_minuty:
            osby = liczba
    return osoby, slonce, t_zewn

class Symulacja:
    """Symulacja pokoju sterowanego przez sterownik rozmyty.

    W każdym kroku: odczytuje warunki, liczby sterowanie metodą rozytą,
    aktualizuje pokój i zapisuje wynik w historii.
    """
    def __init__(self):
        """Tworzy sterownik, pokój i pustą historię.

        Parametry:
        brak

        Zwraca:
        None
        """
        self.symulator, _ = zbuduj_system()
        self.pokoj = Pokoj()
        self.minuta = 0
        self.historia = {
            "godzina": [], "temperatura": [], "t_zewn": [], "wilgotnosc": [], "osoby": [], "slonce": [], "moc": [], "wentylator": [],
        }
    def krok(self):
        """Wykonuje jeden krok (jedną minutę symulacji,

        Parametry:
        brak

        Zwraca:
        None
        """
        osoby, slonce, t_zewn = scenariusz(self.minuta)
        moc, wentylator = oblicz_sterowanie(
            self.symulator, self.pokoj.temperatura, self.pokoj.wilgotnosc, osoby, slonce
        )
        h = self.historia
        h["godzina"].append(GODZINA_START + self.minuta / 60)
        h["temperatura"].append(self.pokoj.temperatura)
        h["t_zewn"].append(t_zewn)
        h["wilgotnosc"].append(self.pokoj.wilgotnosc)
        h["osoby"].append(osoby)
        h["slonce"].append(slonce)
        h["moc"].append(moc)
        h["wentylator"].append(wentylator)
        self.pokoj.krok(moc, wentylator, osoby, slonce, t_zewn)
        self.minuta += 1

    def zakonczona(self):
        """Sprawdza, czy symulacja dobiegła końca.

        Parametry:
        brak

        Zwraca:
        bool: True, jeśli wykonuje wszystkie zaplanowane kroki
        """
        return self.minuta >= LICZBA_MINUT

    def rysuj_wykresy(osie, h):
        """Rysuje cztery wykresy symulacji na podanych osiach.

        Parametry:
        osie (ndarray): Tablica 2x2 osi matplotlib
        h (dict): Historia symulacji (słownik list z klasy Symulacja)

        Zwraca:
        None
        """
        x = h["godzina"]
        for ax in osie.flat:
            ax.clear()
            ax.set_xlim(GODZINA_START, GODZINA_START + LICZBA_MINUT / 60)
            ax.set_xlabel("godzina")
            ax.grid(alpha=0.3)
        ax = osie[0, 0]
        ax.plot(x, h["temperatura"], label="w pokoju", color="tab:red")
        ax.plot(x, h["t_zewn"], label="na zewnątrz", color="tab:gray", linestyle="--")
        ax.axhline(TEMPERATURA_DOCELOWA, color="tab:green", linestyle=":", label="docelowa")
        ax.set_ylim(15, 40)
        ax.set_ylabel("temperatura [C]")
        ax.set_title("Temperatura")
        ax.legend(loc="upper left")

        ax = osie[0, 1]
        ax.plot(x, h["moc"], label="moc chłodzenia", color="tab:blue")
        ax.plot(x, h["wentylator"], label="wentylator", color="tab:orange")
        ax.set_ylim(0.100)
        ax.set_ylabel("[%]")
        ax.set_title("Sterowanie rozmyte (wyjścia)")
        ax.legend(loc="upper left")

        ax = osie[1, 0]
        ax.plot(x, h["slonce"], label="nasłonecznienie", color="gold")
        ax.plot(x, h["wilgotnosc"], label="wilgotność", color="tab:cyan")
        ax.set_ylim(0, 100)
        ax.set_ylabel("[%]")
        ax.set_title("Słońce i wilgotność (wejścia)")
        ax.legend(loc="upper left")

        ax = osie[1, 1]
        ax.step(x, h["osoby"], where="post", color="tab:purple")
        ax.set_ylim(0, 20)
        ax.set_ylabel("liczba osób")
        ax.set_title("Osoby w pokoju (wejscie)")
    def uruchom_na_zywo():
        """Uruchamia symulację na zywo..."""
