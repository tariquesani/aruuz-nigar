"""
Meter definitions for Urdu poetry.

This module contains all meter patterns, names, and foot definitions.
"""

from typing import List, Tuple, NamedTuple, Dict
from aruuz.models import Feet


class Meter(NamedTuple):
    """Represents a meter with its pattern and Urdu name."""
    pattern: str
    name: str


class Foot(NamedTuple):
    """Represents a foot (rukn) with its pattern code and Urdu name."""
    pattern: str
    name: str


# Constants
# NUM_METERS will be set from len(_METERS_DATA) below
NUM_VARIED_METERS = 0
NUM_RUBAI_METERS = 12
NUM_SPECIAL_METERS = 11

# Meter ID array (for reference, not used in Phase 1)
METER_IDS = [
    13, 14, 15, 16, 17, 2, 2, 4, 4, 4, 4, 18, 19, 3, 3, 20, 21, 22, 23, 5, 5, 5, 24, 25, 26, 27, 6, 6, 6, 6, 30, 31, 32, 33, 34, 35, 35, 35, 35, 36, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50,
    51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 7, 103, 64, 65, 8, 8, 8, 8, 9, 9, 9, 9, 10, 10, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 1, 1, 1, 1, 11, 11, 78, 79, 80, 81, 12, 12, 12, 12, 12,
    82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 36, 96, 97, 98, 99, 100, 101, 102, 103, 104
]

# Usage flags (1 = used, 0 = not used)
USAGE = [
    1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1
]

# Internal unified structure - all meter data
_METERS_DATA = [
    Meter(pattern="-===/-===/-===/-===", name="ہزج مثمن سالم"),
    Meter(pattern="-===/-===/-===/-==", name="ہزج مثمن محذوف"),
    Meter(pattern="-=-=/-=-=/-=-=/-=-=", name="ہزج مثمن مقبوض"),
    Meter(pattern="=-=/-===+=-=/-===", name="ہزج مثمن اشتر"),
    Meter(pattern="-=-=/-===/-=-=/-===", name="ہزج مثمن مقبوض سالم"),
    Meter(pattern="==-/-==-/-==-/-===", name="ہزج مثمن اخرب مکفوف سالم"),
    Meter(pattern="==-/-===+==-/-===", name="ہزج مثمن اخرب سالم"),
    Meter(pattern="==-/-==-/-==-/-==", name="ہزج مثمن اخرب مکفوف محذوف"),
    Meter(pattern="===/==-/-==-/-==", name="ہزج مثمن اخرب مکفوف محذوف"),
    Meter(pattern="==-/-===/==-/-==", name="ہزج مثمن اخرب مکفوف محذوف"),
    Meter(pattern="==-/-==-/-===/==", name="ہزج مثمن اخرب مکفوف محذوف"),
    Meter(pattern="-===/-===/-===", name="ہزج مسدس سالم"),
    Meter(pattern="-===/-===/-==", name="ہزج مسدس محذوف"),
    Meter(pattern="==-/-=-=/-==", name="ہزج مسدس اخرب مقبوض محذوف"),
    Meter(pattern="===/=-=/-==", name="ہزج مسدس اخرم اشتر محذوف"),
    Meter(pattern="=-=/-=-=+=-=/-=-=", name="ہزج مربع اشتر مقبوض مضاعف"),
    Meter(pattern="-===/-==", name="ہزج مربع محذوف"),
    Meter(pattern="-===/-==+-===/-==", name="ہزج مربع محذوف مضاعف"),
    Meter(pattern="==-=/==-=/==-=/==-=", name="رجز مثمن سالم"),
    Meter(pattern="=--=/=--=/=--=/=--=", name="رجز مثمن مطوی"),
    Meter(pattern="=--=/-=-=+=--=/-=-=", name="رجز مثمن مطوی مخبون"),
    Meter(pattern="-=-=/=--=+-=-=/=--=", name="رجز مثمن مخبون مطوی"),
    Meter(pattern="==-=/==-=/==-=", name="رجز مسدس سالم"),
    Meter(pattern="=--=/=--=/=--=", name="رجز مسدس مطوی"),
    Meter(pattern="=-==/=-==/=-==/=-==", name="رمل مثمن سالم"),
    Meter(pattern="=-==/=-==/=-==/=-=", name="رمل مثمن محذوف"),
    Meter(pattern="=-==/--==/--==/--=", name="رمل مثمن سالم مخبون محذوف"),
    Meter(pattern="--==/--==/--==/--=", name="رمل مثمن سالم مخبون محذوف"),
    Meter(pattern="=-==/--==/--==/==", name="رمل مثمن مخبون محذوف مقطوع"),
    Meter(pattern="--==/--==/--==/==", name="رمل مثمن مخبون محذوف مقطوع"),
    Meter(pattern="--=-/=-==+--=-/=-==", name="رمل مثمن مشکول"),
    Meter(pattern="==-/=-==+==-/=-==", name="رمل مثمن مشکول مسکّن"),
    Meter(pattern="--==/--==/--==/--==", name="رمل مثمن مخبون"),
    Meter(pattern="=-==/=-==/=-==", name="رمل مسدس سالم"),
    Meter(pattern="=-==/=-==/=-=", name="رمل مسدس محذوف"),
    Meter(pattern="=-==/--==/--=", name="رمل مسدس مخبون محذوف"),
    Meter(pattern="=-==/--==/==", name="رمل مسدس مخبون محذوف مسکن"),
    Meter(pattern="--==/--==/--=", name="رمل مسدس مخبون محذوف"),
    Meter(pattern="--==/--==/==", name="رمل مسدس مخبون محذوف مسکن"),
    Meter(pattern="--==/--==/--==", name="رمل مسدس مخبون"),
    Meter(pattern="-==/-==/-==/-==", name="متقارب مثمن سالم"),
    Meter(pattern="-==/-==/-==/-==/-==/-==/-==/-==", name="متقارب مثمن سالم مضاعف"),
    Meter(pattern="-==/-==/-==/-=", name="متقارب مثمن محذوف"),
    Meter(pattern="=-/-=-/-=-/-==", name="متقارب مثمن اثرم مقبوض"),
    Meter(pattern="=-/-=-/-=-/-=", name="متقارب مثمن اثرم مقبوض محذوف"),
    Meter(pattern="=-/-=-/-=-/-=-/-=-/-=-/-=-/-=", name="متقارب مثمن اثرم مقبوض مضاعف"),
    Meter(pattern="=-/-=-/-=-/-=-/-=-/-=-/-=-/-==", name="متقارب مثمن اثرم مقبوض محذوف مضاعف"),
    Meter(pattern="-==/-==/-==", name="متقارب مسدس سالم"),
    Meter(pattern="-==/-==/-=", name="متقارب مسدس محذوف"),
    Meter(pattern="==/-==/==/-==", name="متقارب مربع اثلم سالم مضاعف"),
    Meter(pattern="=-=/=-=/=-=/=-=", name="متدارک مثمن سالم"),
    Meter(pattern="--=/--=/--=/--=", name="متدارک مثمن مخبون"),
    Meter(pattern="--=/--=/--=/--=/--=/--=/--=/--=", name="متدارک مثمن مخبون مضاعف"),
    Meter(pattern="=-=/=-=/=-=/--=", name="متدارک مثمن سالم مقطوع"),
    Meter(pattern="=-=/=-=/=-=", name="متدارک مسدس سالم"),
    Meter(pattern="=-=/-=/=-=/-=", name="متدارک مربع مخلع مضاعف"),
    Meter(pattern="--=-=/--=-=/--=-=/--=-=", name="کامل مثمن سالم"),
    Meter(pattern="--=-=/--=-=/--=-=", name="کامل مسدس سالم"),
    Meter(pattern="-=--=/-=--=/-=--=/-=--=", name="وافر مثمن سالم"),
    Meter(pattern="-=--=/-=--=/-=--=", name="وافر مسدس سالم"),
    Meter(pattern="-=--=/-=--=/-==", name="وافر مسدس مقطوف"),
    Meter(pattern="-===/=-==/-===/=-==", name="مضارع مثمن سالم"),
    Meter(pattern="-==-/=-=-/-==-/=-=", name="مضارع مثمن مکفوف محذوف"),
    Meter(pattern="==-/=-==/==-/=-==", name="مضارع مثمن اخرب"),
    Meter(pattern="==-/=-=-/-==-/=-=", name="مضارع مثمن اخرب مکفوف محذوف"),
    Meter(pattern="==-/=-==/==-/=-=", name="مضارع مثمن اخرب محذوف"),
    Meter(pattern="==-/=-=-/-===", name="مضارع مسدس اخرب مکفوف"),
    Meter(pattern="==-=/=-==/==-=/=-==", name="مجتث مثمن سالم"),
    Meter(pattern="-=-=/--==/-=-=/--==", name="مجتث مثمن مخبون"),
    Meter(pattern="-=-=/===/-=-=/--==", name="مجتث مثمن مخبون"),
    Meter(pattern="-=-=/--==/-=-=/===", name="مجتث مثمن مخبون"),
    Meter(pattern="-=-=/===/-=-=/===", name="مجتث مثمن مخبون"),
    Meter(pattern="-=-=/--==/-=-=/--=", name="مجتث مثمن مخبون محذوف"),
    Meter(pattern="-=-=/===/-=-=/--=", name="مجتث مثمن مخبون محذوف"),
    Meter(pattern="-=-=/--==/-=-=/==", name="مجتث مثمن مخبون محذوف مسکن"),
    Meter(pattern="-=-=/===/-=-=/==", name="مجتث مثمن مخبون محذوف مسکن"),
    Meter(pattern="-=-=/--==/-=-=", name="مجتث مسدس مخبون"),
    Meter(pattern="-=-=/===/-=-=", name="مجتث مسدس مخبون"),
    Meter(pattern="==-=/===-/==-=/===-", name="منسرح مثمن سالم"),
    Meter(pattern="=--=/=-=+=--=/=-=", name="منسرح مثمن مطوی مکسوف"),
    Meter(pattern="=--=/=-=-/=--=/=", name="منسرح مثمن مطوی منحور"),
    Meter(pattern="=--=/=-=/=--=", name="منسرح مسدس مطوی مکسوف"),
    Meter(pattern="===-/==-=/===-/==-=", name="مقتضب مثمن سالم"),
    Meter(pattern="=-=-/=--=/=-=-/=--=", name="مقتضب مثمن مطوی"),
    Meter(pattern="==-=/==-=/===-", name="سریع مسدس سالم"),
    Meter(pattern="=--=/=--=/=-=", name="سریع مسدس مطوی مکسوف"),
    Meter(pattern="==-=/==-=/-==", name="سریع مسدس مخبون مکسوف"),
    Meter(pattern="=-==/==-=/=-==/==-=", name="خفیف مثمن سالم"),
    Meter(pattern="=-==/==-=/=-==", name="خفیف مسدس سالم"),
    Meter(pattern="--==/-=-=/--==", name="خفیف مسدس مخبون"),
    Meter(pattern="=-==/-=-=/--=", name="خفیف مسدس مخبون محذوف"),
    Meter(pattern="--==/-=-=/--=", name="خفیف مسدس مخبون محذوف"),
    Meter(pattern="=-==/-=-=/==", name="خفیف مسدس مخبون محذوف مقطوع"),
    Meter(pattern="--==/-=-=/==", name="خفیف مسدس مخبون محذوف مقطوع"),
    Meter(pattern="=-==/-=-=/=", name="خفیف مسدس سالم مخبون محجوف"),
    Meter(pattern="--==/-=-=/=", name="خفیف مسدس مخبون محجوف"),
    Meter(pattern="-===/-==/-===", name="طویل مثمن سالم"),
    Meter(pattern="-==/-===/-==/-=-=", name="طویل مثمن سالم مقبوض"),
    Meter(pattern="-==/-=-=/-==/-=-=", name="طویل مثمن مقبوض"),
    Meter(pattern="=-==/=-=/=-==/=-=", name="مدید مثمن سالم"),
    Meter(pattern="--==/--=/--==/--=", name="مدید مثمن مخبون"),
    Meter(pattern="--==/==/--==/--=", name="مدید مثمن مخبون"),
    Meter(pattern="===/--=/--==/--=", name="مدید مثمن مخبون"),
    Meter(pattern="--==/--=/===/--=", name="مدید مثمن مخبون"),
    Meter(pattern="--==/--=/--==/==", name="مدید مثمن مخبون"),
    Meter(pattern="=-==/--=/=-==/--=", name="مدید مثمن سالم مخبون"),
    Meter(pattern="==-=/=-=/==-=/=-=", name="بسیط مثمن سالم"),
    Meter(pattern="-=-=/--=/-=-=/--=", name="بسیط مثمن مخبون"),
    Meter(pattern="-===/-===/=-==", name="قریب مسدس سالم"),
    Meter(pattern="==-/-==-/=-==", name="قریب مسدس اخرب مکفوف"),
    Meter(pattern="=-==/=-==/==-=", name="جدید مسدس سالم"),
    Meter(pattern="--==/--==/-=-=", name="جدید مسدس مخبون"),
    Meter(pattern="=-==/-===/-===", name="مشاکل مسدس سالم"),
    Meter(pattern="=-=-/-==-/-==", name="مشاکل مسدس مکفوف محذوف"),
    Meter(pattern="-=-==/-=-==/-=-==/-=-==", name="جمیل مثمن سالم"),
    Meter(pattern="=-=/-===", name="ہزج مربع اشتر"),
    Meter(pattern="=-=/-=-=", name="ہزج مربع اشتر مقبوض"),
    Meter(pattern="-===/-===", name="ہزج مربع سالم"),
    Meter(pattern="-=-=/-=-=/-=-=/-=", name="ہزج مثمن مقبوض محذوف"),
    Meter(pattern="=-==/--==/--==", name="رمل مسدس مخبون"),
    Meter(pattern="-===/-===", name="ہزج مربع سالم"),
    Meter(pattern="=-==/=-==", name="رمل مربع سالم"),
    Meter(pattern="=-==/=-=", name="ہزج مربع محذوف"),
    Meter(pattern="-==/-==", name="متقارب مربع سالم"),
    Meter(pattern="--=-=/--=-=", name="کامل مربع سالم"),
    Meter(pattern="-==/-===", name="طویل مربع سالم"),
    Meter(pattern="=-==/=-=", name="مدید مربع سالم"),
    Meter(pattern="-===/-===/-===/-===/-===/-===/-===/-===", name="ہزج مثمن سالم مضاعف"),
    Meter(pattern="-=-==/-=-==", name="جمیل مربع سالم")
]

# Backward compatibility: derived lists for existing code
METERS = [m.pattern for m in _METERS_DATA]
METER_NAMES = [m.name for m in _METERS_DATA]
NUM_METERS = len(_METERS_DATA)

# Optional: alias for clarity (METERS already contains patterns)
METER_PATTERNS = METERS

# Validation: ensure counts match and data integrity
assert len(_METERS_DATA) == 129, f"Expected 129 meters, found {len(_METERS_DATA)}"
assert len(METERS) == NUM_METERS, "METERS length mismatch"
assert len(METER_NAMES) == NUM_METERS, "METER_NAMES length mismatch"
assert NUM_METERS == 129, "NUM_METERS should be 129"

# Varied meters (for future use)
METERS_VARIED = [
    "--==/-=-=/==",
    "--==/-=-=/--=",
    "--==/--==/==",
    "--==/--==/--=",
    "--==/--==/--==/==",
    "--==/--==/--==/--=",
    "--==/--==/--=="
]

METERS_VARIED_NAMES = [
    "خفیف مسدّس مخبون محذوف مقطوع",
    "خفیف مسدّس مخبون محذوف",
    "رمل مسدّس مخبون محذوف مقطوع",
    "رمل مسدّس مخبون محذوف",
    "رمل مثمّن مخبون محذوف مقطوع",
    "رمل مثمّن مخبون محذوف",
    "رمل مسدس مخبون"
]

# Rubai meters
RUBAI_METERS = [
    "==-/-==-/-==-/-=",
    "==-/-==-/-===/=",
    "==-/-=-=/-===/=",
    "==-/-=-=/-==-/-=",
    "===/=-=/-==-/-=",
    "===/=-=/-===/=",
    "==-/-===/===/=",
    "==-/-===/==-/-=",
    "===/===/==-/-=",
    "===/===/===/=",
    "===/==-/-===/=",
    "===/==-/-==-/-="
]

RUBAI_METER_NAMES = [
    "ہزج مثمّن اخرب مکفوف مجبوب",
    "ہزج مثمّن اخرب مکفوف ابتر",
    "ہزج مثمّن اخرب مقبوض ابتر",
    "ہزج مثمّن اخرب مقبوض مکفوف مجبوب",
    "ہزج مثمّن اخرم اشتر مکفوف مجبوب",
    "ہزج مثمّن اخرم اشتر ابتر",
    "ہزج مثمّن اخرب اخرم ابتر",
    "ہزج مثمّن اخرب مجبوب",
    "ہزج مثمّن اخرم اخرب مجبوب",
    "ہزج مثمّن اخرم ابتر",
    "ہزج مثمّن اخرم اخرب ابتر",
    "ہزج مثمّن اخرم اخرب مکفوف مجبوب"
]

# Special meters (Hindi/Zamzama)
SPECIAL_METERS = [
    "=(=)/=(=)/=(=)/=(=)/=(=)/=(=)/=(=)/=",
    "=(=)/=(=)/=(=)/=(=)/=(=)/=",
    "=(=)/=(=)/=(=)/=(=)/=(=)/=(=)/=(=)/==",
    "=(=)/=(=)/=(=)/=",
    "=(=)/=(=)/=(=)/==",
    "=(=)/=(=)/=",
    "=(=)/=(=)/=(=)/=(=)/=(=)/==",
    "=(=)/=(=)",
    "(=)=/(=)=/(=)=/(=)=/(=)=/(=)=/(=)=/(=)=",
    "(=)=/(=)=/(=)=/(=)=/(=)=/(=)=",
    "(=)=/(=)=/(=)=/(=)"
]

SPECIAL_METERS_AFAIL = [
    "فعلن فعلن فعلن فعلن فعلن فعلن فعلن فع",
    "فعلن فعلن فعلن فعلن فعلن فع",
    "فعلن فعلن فعلن فعلن فعلن فعلن فعلن فعلن",
    "فعلن فعلن فعلن فع",
    "فعلن فعلن فعلن فعلن",
    "فعلن فعلن فع",
    "فعلن فعلن فعلن فعلن فعلن فعلن",
    "فعلن فعلن",
    "فعلن فعلن فعلن فعلن فعلن فعلن فعلن فعلن",
    "فعلن فعلن فعلن فعلن فعلن فعلن",
    "فعلن فعلن فعلن فعلن"
]

SPECIAL_METER_NAMES = [
    "بحرِ ہندی/ متقارب مثمن مضاعف",
    "بحرِ ہندی/ متقارب مسدس مضاعف",
    "بحرِ ہندی/ متقارب اثرم مقبوض محذوف مضاعف",
    "بحرِ ہندی/ متقارب مربع مضاعف",
    "بحرِ ہندی/ متقارب اثرم مقبوض محذوف",
    "بحرِ ہندی/ متقارب مثمن محذوف",
    "بحرِ ہندی/ متقارب مسدس محذوف",
    "بحرِ ہندی/ متقارب مربع محذوف",
    "بحرِ زمزمہ/ متدارک مثمن مضاعف",
    "بحرِ زمزمہ/ متدارک مسدس مضاعف",
    "بحرِ زمزمہ/ متدارک مربع مضاعف"
]

# Internal unified structure - all foot data
_FEET_DATA = [
    Foot(pattern="===", name="مفعولن"),
    Foot(pattern="==-=", name="مستفعلن"),
    Foot(pattern="==-", name="مفعول"),
    Foot(pattern="==", name="فِعْلن"),
    Foot(pattern="=-==", name="فاعلاتن"),
    Foot(pattern="=-=-", name="فاعلاتُ"),
    Foot(pattern="=-=", name="فاعلن"),
    Foot(pattern="=--=", name="مفتَعِلن"),
    Foot(pattern="=-", name="فِعْل"),
    Foot(pattern="=", name="فِع"),
    Foot(pattern="-===", name="مفاعیلن"),
    Foot(pattern="-==-", name="مفاعیل"),
    Foot(pattern="-==", name="فعولن"),
    Foot(pattern="-=-=", name="مفاعلن"),
    Foot(pattern="-=-", name="فعول"),
    Foot(pattern="-=", name="فَعَل"),
    Foot(pattern="--==", name="فَعِلاتن"),
    Foot(pattern="--=-=", name="متَفاعلن"),
    Foot(pattern="--=-", name="فَعِلات"),
    Foot(pattern="--=", name="فَعِلن"),
    Foot(pattern="-=-==", name="مَفاعلاتن"),
    Foot(pattern="===-", name="مفعولاتُ"),
    Foot(pattern="-=--=", name="مفاعِلَتن"),
    Foot(pattern="==-=-", name="مستفعلان"),
    Foot(pattern="=-==-", name="فاعلاتان"),
    Foot(pattern="=--=-", name="مفتَعِلان"),
    Foot(pattern="-===-", name="مفاعیلان"),
    Foot(pattern="-=-=-", name="مفاعلان"),
    Foot(pattern="--==-", name="فَعِلاتان"),
    Foot(pattern="--=-=-", name="متَفاعلان"),
    Foot(pattern="-=-==-", name="مَفاعلاتان"),
    Foot(pattern="-=--=-", name="مفاعِلَتان")
]

# Backward compatibility: derived lists for existing code
FEET = [f.pattern for f in _FEET_DATA]
FEET_NAMES = [f.name for f in _FEET_DATA]

# Performance optimization: dictionaries for O(1) lookups
CODE_TO_NAME: Dict[str, str] = {f.pattern: f.name for f in _FEET_DATA}
NAME_TO_CODE: Dict[str, str] = {f.name: f.pattern for f in _FEET_DATA}

# Validation: ensure counts match and data integrity
assert len(_FEET_DATA) == 32, f"Expected 32 feet, found {len(_FEET_DATA)}"
assert len(FEET) == len(_FEET_DATA), "FEET length mismatch"
assert len(FEET_NAMES) == len(_FEET_DATA), "FEET_NAMES length mismatch"
assert len(CODE_TO_NAME) == len(_FEET_DATA), "CODE_TO_NAME dictionary size mismatch"
assert len(NAME_TO_CODE) == len(_FEET_DATA), "NAME_TO_CODE dictionary size mismatch"


def meter_index(meter_name: str) -> List[int]:
    """
    Find indices of meters matching the given meter name.
    
    Args:
        meter_name: Name of the meter in Urdu
        
    Returns:
        List of indices where the meter name matches
    """
    indices = []
    for i, meter in enumerate(_METERS_DATA):
        if meter.name == meter_name:
            indices.append(i)
    return indices


def afail(meter: str) -> str:
    """
    Convert meter pattern to foot names (afail).
    
    Args:
        meter: Meter pattern string (e.g., "-===/-===/-===/-===")
        
    Returns:
        String of foot names separated by spaces
    """
    feet_str = ""
    for part in meter.split('+'):
        for foot_pattern in part.split('/'):
            name = CODE_TO_NAME.get(foot_pattern)
            if name:
                feet_str += " " + name
    return feet_str.strip()


def afail_list(meter: str) -> List[Feet]:
    """
    Convert meter pattern to list of Feet objects with names and codes.
    
    Args:
        meter: Meter pattern string (e.g., "-===/-===/-===/-===")
        
    Returns:
        List of Feet objects, each containing foot name and code
    """
    feet_list = []
    for part in meter.split('+'):
        for foot_pattern in part.split('/'):
            name = CODE_TO_NAME.get(foot_pattern)
            if name:
                feet_obj = Feet()
                feet_obj.foot = name
                feet_obj.code = foot_pattern
                feet_list.append(feet_obj)
    return feet_list


def afail_hindi(meter_name: str) -> str:
    """
    Get afail for Hindi/Zamzama special meters.
    
    Args:
        meter_name: Name of the special meter
        
    Returns:
        Afail string for the special meter
    """
    for i in range(NUM_SPECIAL_METERS):
        if SPECIAL_METER_NAMES[i] == meter_name:
            return SPECIAL_METERS_AFAIL[i]
    return ""


def rukn(code: str) -> str:
    """
    Convert scansion code to foot name (rukn).
    
    Args:
        code: Scansion code (e.g., "===", "==-")
        
    Returns:
        Foot name in Urdu, or empty string if not found
    """
    # Replace 'x' with '=' for matching
    code = code.replace('x', '=')
    return CODE_TO_NAME.get(code, "")


def rukn_code(name: str) -> str:
    """
    Convert foot name to scansion code.
    
    Args:
        name: Foot name in Urdu
        
    Returns:
        Scansion code pattern, or empty string if not found
    """
    name = name.strip()
    return NAME_TO_CODE.get(name, "")


def zamzama_feet(index: int, code: str) -> Tuple[str, List[Feet]]:
    """
    Generate foot names for Zamzama meters from scansion code.
    
    Args:
        index: Special meter index (8-10 for Zamzama)
        code: Scansion code string (e.g., "==-==-==-==-==-==-==-==")
        
    Returns:
        Space-separated string of foot names in Urdu
        
    Note:
        This function matches the C# zamzamaFeet() implementation logic:
        - Pattern "--=" maps to " فَعِلن"
        - Pattern "==" maps to " فعْلن"
    """
    feet_names: List[str] = []
    feet_list: List[Feet] = []
    
    # Remove trailing '-' if present
    if code and code[-1] == '-':
        code = code[:-1]
    
    len_code = len(code)
    
    # Iterate through code character by character
    # Matches C# for loop: for (int i = 0; i < len; i++)
    i = 0
    while i < len_code:
        if code[i] == '-':
            # Check for pattern: --= (two dashes followed by equals)
            # In C#: if(code[++i].Equals('-')) then if(code[++i].Equals('='))
            # This means: check code[i+1] == '-', then check code[i+2] == '='
            if i + 1 < len_code:
                i += 1  # Pre-increment equivalent: ++i
                if code[i] == '-':
                    if i + 1 < len_code:
                        i += 1  # Pre-increment again: ++i
                        if code[i] == '=':
                            feet_names.append("فَعِلن")
                            feet_list.append(Feet(foot="فَعِلن", code="--="))
                            # At this point i points to the '=' character
                            # The loop will increment i, so we'll skip past this pattern
                        else:
                            break
                    else:
                        break
                else:
                    break
            else:
                break
        else:
            # Check for pattern: == (two equals)
            # In C#: if(code[++i].Equals('='))
            # This means: check code[i+1] == '='
            if i + 1 < len_code:
                i += 1  # Pre-increment equivalent: ++i
                if code[i] == '=':
                    feet_names.append("فعْلن")
                    feet_list.append(Feet(foot="فعْلن", code="=="))
                else:
                    break
            else:
                break
        i += 1  # Loop increment (equivalent to for loop i++)
    
    return " ".join(feet_names), feet_list


def hindi_feet(index: int, code: str) -> Tuple[str, List[Feet]]:
    """
    Generate foot names for Hindi meters from scansion code.
    
    Args:
        index: Special meter index (0-7 for Hindi)
        code: Scansion code string
        
    Returns:
        Space-separated string of foot names in Urdu, or empty string if validation fails
        
    Note:
        This function matches the C# hindiFeet() implementation logic:
        - Uses greedy pattern matching (tries patterns in order, first match wins)
        - Validates foot count based on index:
          - index 0: 8 feet
          - index 1: 6 feet
          - index 2: 8 feet
          - index 3: 4 feet
          - index 4: 4 feet
          - index 5: 3 feet
          - index 6: 6 feet
          - index 7: 2 feet
    """
    feet_names: List[str] = []
    feet_list: List[Feet] = []
    num_feet = 0
    
    # Foot patterns and their corresponding names
    # Order matters: patterns are tried in this order
    afail_patterns = ["==", "=-", "-==", "-=-", "-=", "=", "==-", "-==-"]
    afail_names = ["فعلن", "فعْل", "فعولن", "فعول", "فَعَل", "فع", "فعْلان", "فعولان"]
    
    # Expected foot counts for each index
    expected_feet = {
        0: 8,
        1: 6,
        2: 8,
        3: 4,
        4: 4,
        5: 3,
        6: 6,
        7: 2
    }
    
    # Validate index
    if index not in expected_feet:
        return "", []
    
    # Remove trailing '-' if present
    if code and code[-1] == '-':
        code = code[:-1]
    
    code_len = len(code)
    
    if code_len == 0:
        return "", []
    
    # Iterate through code character by character
    j = 0
    while j < code_len:
        index_found = -1
        
        # Try to match each pattern in order
        for k in range(len(afail_patterns)):
            pattern = afail_patterns[k]
            pattern_len = len(pattern)
            
            # Check if pattern fits at current position
            if j + pattern_len > code_len:
                continue
            
            # Check if pattern matches at position j
            flag = True
            for z in range(pattern_len):
                if code[j + z] != pattern[z]:
                    flag = False
                    break
            
            if flag:
                index_found = k
                break  # First match wins
        
        if index_found >= 0:
            # Add the matched foot name and corresponding code pattern
            name = afail_names[index_found]
            pattern = afail_patterns[index_found]
            feet_names.append(name)
            feet_list.append(Feet(foot=name, code=pattern))
            num_feet += 1
            # Move j forward by pattern length - 1 (the loop will increment it by 1)
            j += len(afail_patterns[index_found]) - 1
        else:
            # No pattern matched, break
            break
        
        j += 1  # Move to next character
    
    # Validate foot count
    if num_feet == expected_feet[index]:
        return " ".join(feet_names), feet_list
    else:
        return "", []