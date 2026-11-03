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

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# Temperatura, do której dąży klimatyzacja (C)
TEMPERATURA_DOCELOWA = 24.0
# Temperatura w pokoju na początku symulacji (C)
TEMPERATURA_POCZATKOWA =  27.0
# Godzina rozpoczęcia symulacji
GODZINA_START = 8
# Długość symulacji w minutach (8:00 - 20:00)
LICZBA_MINUT = 720
#Ile minut symulacji przypada na jedną klatkę animacji
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
     osoby["duzo"] = fuzz.trapmf(osoby.universe, [10, 15, 20, 20,])

     slonce["slabe"] = fuzz.trapmf(slonce.universe, [0, 0, 20, 45])
     slonce["srednie"] = fuzz.trimf(slonce.universe, [25, 50, 75])
     slonce["mocne"] = fuzz.trapmf(slonce.universe, [55, 80, 100, 100])

     for wyjscie in (moc, wentylator):
         wyjscie["mala"] = fuzz.trimf(wyjscie.universe, [0, 0, 40])
         wyjscie["srednia"] = fuzz.trimf(wyjscie.universe, [20, 50, 80])
         wyjscie["duza"] = fuzz.trimf(wyjscie.universe, [60, 100, 100])