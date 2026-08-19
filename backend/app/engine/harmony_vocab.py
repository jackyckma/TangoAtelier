"""Explicit chord vocabulary — root + intervals, no scale-degree inference."""

from __future__ import annotations

from dataclasses import dataclass

# Legacy symbols emitted by older templates / UI locks
SYMBOL_ALIASES: dict[str, str] = {
    "VII": "bVII",
    "iiø": "iiø7",
}


@dataclass(frozen=True)
class ChordSpec:
    symbol: str
    root_semitones: int
    intervals: tuple[int, ...]
    function: str
    label_zh: str
    label_en: str


MINOR_VOCAB: dict[str, ChordSpec] = {
    "i": ChordSpec("i", 0, (0, 3, 7), "tonic", "主和弦", "tonic minor"),
    "ii": ChordSpec("ii", 2, (0, 3, 7), "subdominant", "二級小三", "supertonic minor"),
    "iiø7": ChordSpec("iiø7", 2, (0, 3, 6, 10), "subdominant", "半減七", "half-diminished 7th"),
    "ii°": ChordSpec("ii°", 2, (0, 3, 6), "subdominant", "二級減三", "diminished triad"),
    "iii": ChordSpec("iii", 3, (0, 3, 7), "tonic", "三級小三", "mediant minor"),
    "III": ChordSpec("III", 3, (0, 4, 7), "tonic", "關係大三", "relative major"),
    "III+": ChordSpec("III+", 3, (0, 4, 8), "colour", "增三和弦", "augmented"),
    "iv": ChordSpec("iv", 5, (0, 3, 7), "subdominant", "下屬小三", "minor subdominant"),
    "iv6": ChordSpec("iv6", 5, (0, 3, 7, 9), "subdominant", "下屬小六", "minor 6th"),
    "IV": ChordSpec("IV", 5, (0, 4, 7), "subdominant", "大下屬（多利安色彩）", "major IV (dorian)"),
    "v": ChordSpec("v", 7, (0, 3, 7), "dominant", "自然小五級", "natural minor v"),
    "V": ChordSpec("V", 7, (0, 4, 7), "dominant", "屬和弦", "dominant"),
    "V7": ChordSpec("V7", 7, (0, 4, 7, 10), "dominant", "屬七", "dominant 7th"),
    "V7b9": ChordSpec("V7b9", 7, (0, 4, 7, 10, 13), "dominant", "屬七降九", "dominant 7♭9"),
    "vi": ChordSpec("vi", 9, (0, 3, 7), "subdominant", "六級小三", "submediant minor"),
    "VI": ChordSpec("VI", 8, (0, 4, 7), "subdominant", "六級大三", "submediant major"),
    "bVII": ChordSpec("bVII", 10, (0, 4, 7), "subdominant", "降七級大三", "flat-VII"),
    "vii°": ChordSpec("vii°", 11, (0, 3, 6), "dominant", "導音減三", "leading-tone dim"),
    "vii°7": ChordSpec("vii°7", 11, (0, 3, 6, 9), "dominant", "導七減七", "fully-diminished 7th"),
    "V7/iv": ChordSpec("V7/iv", 0, (0, 4, 7, 10), "dominant", "iv 的次屬", "secondary dom of iv"),
    "V7/V": ChordSpec("V7/V", 2, (0, 4, 7, 10), "dominant", "V 的次屬", "secondary dom of V"),
    "V7/VI": ChordSpec("V7/VI", 3, (0, 4, 7, 10), "dominant", "VI 的次屬", "secondary dom of VI"),
    "V7/III": ChordSpec("V7/III", 10, (0, 4, 7, 10), "dominant", "III 的次屬", "secondary dom of III"),
    "bII": ChordSpec("bII", 1, (0, 4, 7), "subdominant", "拿坡里", "Neapolitan"),
    "Ger+6": ChordSpec("Ger+6", 8, (0, 4, 7, 10), "dominant", "德式增六", "German augmented 6th"),
    "It+6": ChordSpec("It+6", 8, (0, 4, 10), "dominant", "義式增六", "Italian augmented 6th"),
    "subV7": ChordSpec("subV7", 1, (0, 4, 7, 10), "dominant", "三全音替代", "tritone substitute"),
    "i6": ChordSpec("i6", 0, (0, 3, 7, 9), "tonic", "小六和弦", "minor 6th"),
    "iM7": ChordSpec("iM7", 0, (0, 3, 7, 11), "tonic", "小大七", "minor-major 7th"),
    "i7": ChordSpec("i7", 0, (0, 3, 7, 10), "tonic", "小七", "minor 7th"),
    "I": ChordSpec("I", 0, (0, 4, 7), "tonic", "畢卡第三音", "Picardy third"),
}

MAJOR_VOCAB: dict[str, ChordSpec] = {
    "I": ChordSpec("I", 0, (0, 4, 7), "tonic", "主和弦", "major tonic"),
    "ii": ChordSpec("ii", 2, (0, 3, 7), "subdominant", "二級小七", "supertonic minor"),
    "iiø7": ChordSpec("iiø7", 2, (0, 3, 6, 10), "subdominant", "二級半減七", "half-diminished 7th"),
    "iii": ChordSpec("iii", 4, (0, 3, 7), "tonic", "三級小三", "mediant minor"),
    "III": ChordSpec("III", 4, (0, 4, 7), "tonic", "三級大三", "mediant major"),
    "IV": ChordSpec("IV", 5, (0, 4, 7), "subdominant", "下屬大三", "subdominant major"),
    "iv": ChordSpec("iv", 5, (0, 3, 7), "subdominant", "借用小下屬", "borrowed minor iv"),
    "V": ChordSpec("V", 7, (0, 4, 7), "dominant", "屬和弦", "dominant"),
    "V7": ChordSpec("V7", 7, (0, 4, 7, 10), "dominant", "屬七", "dominant 7th"),
    "V7b9": ChordSpec("V7b9", 7, (0, 4, 7, 10, 13), "dominant", "屬七降九", "dominant 7♭9"),
    "vi": ChordSpec("vi", 9, (0, 3, 7), "subdominant", "六級小三", "submediant minor"),
    "VI": ChordSpec("VI", 8, (0, 4, 7), "subdominant", "借用大六", "borrowed ♭VI"),
    "bVI": ChordSpec("bVI", 8, (0, 4, 7), "subdominant", "降六級", "flat submediant"),
    "bIII": ChordSpec("bIII", 3, (0, 4, 7), "tonic", "降三級", "flat mediant"),
    "vii°": ChordSpec("vii°", 11, (0, 3, 6), "dominant", "導音減三", "leading-tone dim"),
    "vii°7": ChordSpec("vii°7", 11, (0, 3, 6, 9), "dominant", "導七減七", "fully-diminished 7th"),
    "V7/ii": ChordSpec("V7/ii", 9, (0, 4, 7, 10), "dominant", "ii 的次屬", "secondary dom of ii"),
    "V7/IV": ChordSpec("V7/IV", 5, (0, 4, 7, 10), "dominant", "IV 的次屬", "secondary dom of IV"),
    "V7/V": ChordSpec("V7/V", 2, (0, 4, 7, 10), "dominant", "V 的次屬", "secondary dom of V"),
    "bII": ChordSpec("bII", 1, (0, 4, 7), "subdominant", "拿坡里", "Neapolitan"),
    "subV7": ChordSpec("subV7", 1, (0, 4, 7, 10), "dominant", "三全音替代", "tritone substitute"),
    "i": ChordSpec("i", 0, (0, 3, 7), "tonic", "借用小主", "borrowed minor tonic"),
}


class UnknownChordSymbol(LookupError):
    """Raised when a symbol is absent from the mode vocabulary."""


def normalize_symbol(symbol: str) -> str:
    return SYMBOL_ALIASES.get(symbol, symbol)


def chord_spec(symbol: str, mode: str) -> ChordSpec:
    sym = normalize_symbol(symbol)
    vocab = MINOR_VOCAB if mode == "minor" else MAJOR_VOCAB
    spec = vocab.get(sym)
    if spec is None:
        raise UnknownChordSymbol(f"{symbol!r} not in {mode} vocabulary")
    return spec


def pitch_classes_for_symbol(tonic: int, mode: str, symbol: str) -> frozenset[int]:
    spec = chord_spec(symbol, mode)
    root_pc = (tonic + spec.root_semitones) % 12
    return frozenset((root_pc + iv) % 12 for iv in spec.intervals)


def apply_inversion(pitches: list[int], inversion: int) -> list[int]:
    if inversion <= 0 or len(pitches) < 2:
        return list(pitches)
    ordered = sorted(pitches)
    inv = inversion % len(ordered)
    bass = ordered[inv]
    rest = ordered[inv + 1 :] + [p + 12 for p in ordered[:inv]]
    return [bass, *rest]
