"""Urdu → Roman Urdu transliteration for Hugo novel chapters."""

import re
import os

# ─── Expanded word dictionary (2500+ common Urdu words/forms) ───
# Key insight: Urdu omits short vowels. The dictionary gives the correct form.
WORD_MAP = {
    # Core pronouns & particles
    "میں": "main", "تم": "tum", "تو": "tu", "آپ": "aap",
    "ہم": "hum", "وہ": "woh", "یہ": "yeh", "اس": "is",
    "ان": "in", "انہوں": "unhon", "جس": "jis", "کسی": "kisi",
    "کوئی": "koi", "کچھ": "kuch", "سب": "sab", "کوئ": "koi",
    "جن": "jin", "کن": "kin", "جنہیں": "jinhein",
    "جنھیں": "jinhein", "انہیں": "unhein", "انھیں": "unhein",
    "اسے": "use", "اسے": "ise", "اسی": "isi", "اسی": "usi",
    "انہی": "unhi", "انھی": "unhi", "انہی": "inhin",
    "ان کو": "unko", "اس کو": "usko",
    "تمہیں": "tumhein", "تمھیں": "tumhein",
    "ہمیں": "humein", "ہم کو": "humko",
    "تجھے": "tujhe", "مجھے": "mujhe", "مجھ کو": "mujhko",

    # Places & directions
    "یہاں": "yahan", "وہاں": "wahan", "کہاں": "kahan",
    "جہاں": "jahan", "ادھر": "idhar", "اُدھر": "udhar",
    "کدھر": "kidhar", "جِدھر": "jidhar",
    "اندر": "andar", "باہر": "bahar",
    "اوپر": "oopar", "نیچے": "neeche",
    "آگے": "aage", "پیچھے": "peeche",
    "دائیں": "daein", "بائیں": "baein",
    "سامنے": "samne", "پاس": "paas",

    # Time words
    "اب": "ab", "تب": "tab", "جب": "jab", "کب": "kab",
    "پھر": "phir", "ابھی": "abhi", "کبھی": "kabhi",
    "پہلے": "pehle", "بعد": "baad", "دوران": "doran",
    "آج": "aaj", "کل": "kal", "رات": "raat", "دن": "din",
    "صبح": "subah", "شام": "shaam",
    "سال": "saal", "مہینہ": "mahina", "ہفتہ": "hafta",
    "گھنٹہ": "ghanta", "منٹ": "minute",
    "لمحہ": "lamha", "پل": "pal",
    "دیر": "der", "جلدی": "jaldi",
    "ہمیشہ": "hamesha", "اکثر": "aksar", "کبھی کبھی": "kabhi kabhi",
    "ابھی تک": "abhi tak", "اب تک": "ab tak",
    "تب تک": "tab tak", "جب تک": "jab tak",

    # Verbs — be/have/do
    "ہے": "hai", "ہیں": "hain", "ہو": "ho", "ہوں": "hoon",
    "تھا": "tha", "تھی": "thi", "تھے": "thay", "تھیں": "thin",
    "ہوا": "hua", "ہوئی": "hui", "ہوئے": "huye", "ہوے": "huye",
    "ہونا": "hona", "ہوگا": "hoga", "ہوگی": "hogi", "ہوں گے": "honge",
    "نہیں": "nahin", "نہ": "na", "ہاں": "haan",
    "سکتا": "sakta", "سکتی": "sakti", "سکتے": "sakte", "سکتیں": "saktin",
    "سکے": "sake", "سکی": "saki", "سکو": "sako",
    "چاہیے": "chahiye", "چاہئے": "chahiye",
    "کیا": "kya", "کیوں": "kyun", "کیسے": "kaise",
    "کون": "kaun", "کب": "kab", "کیا": "kiya",
    "کر": "kar", "کرنا": "karna", "کرتا": "karta",
    "کرتی": "karti", "کرتے": "karte", "کرتیں": "kartin",
    "کرو": "karo", "کریں": "karein", "کرے": "kare",
    "کی": "ki", "کیا": "kiya", "کئے": "kiye", "کیں": "kin",
    "ہو": "ho", "ہو": "ho",

    # Verb Root: آ (aa/come)
    "آنا": "aana", "آیا": "aaya", "آئی": "aai", "آئے": "aaye",
    "آؤ": "ao", "آتا": "aata", "آتی": "aati", "آتے": "aate",
    "آؤں": "aaon", "آئے": "aaye", "آئیں": "aaein",
    "آکر": "aakar", "آکے": "aake",

    # Verb Root: جا (ja/go)
    "جانا": "jana", "گیا": "gaya", "گئی": "gai", "گئے": "gaye",
    "جاتا": "jata", "جاتی": "jati", "جاتے": "jate", "جاتے": "jate",
    "جاؤ": "jao", "جائیں": "jaein", "جاؤں": "jaon",
    "جاکر": "jakar", "جا کے": "ja ke",

    # Verb Root: کہ (keh/say)
    "کہنا": "kehna", "کہا": "kaha", "کہی": "kahi", "کہے": "kahe",
    "کہتا": "kehta", "کہتی": "kehti", "کہتے": "kehte", "کہتیں": "kehtin",
    "کہو": "kaho", "کہیں": "kahein",

    # Verb Root: دے (de/give)
    "دینا": "dena", "دیا": "diya", "دی": "di", "دئے": "diye",
    "دیتا": "deta", "دیتی": "deti", "دیتے": "dete", "دیتیں": "detin",
    "دو": "do", "دیں": "dein", "دے": "de",

    # Verb Root: لے (le/take)
    "لینا": "lena", "لیا": "liya", "لی": "li", "لئے": "liye",
    "لیتا": "leta", "لیتی": "leti", "لیتے": "lete", "لیتیں": "letin",
    "لو": "lo", "لوں": "lon", "لیں": "lein", "لے": "le",

    # Verb Root: رکھ (rakh/keep)
    "رکھنا": "rakhna", "رکھا": "rakha", "رکھی": "rakhi",
    "رکھے": "rakhe", "رکھتا": "rakhta", "رکھتی": "rakhti",
    "رکھتے": "rakhte", "رکھو": "rakho", "رکھیں": "rakhein",

    # Verb Root: رہ (reh/stay)
    "رہنا": "rehna", "رہا": "raha", "رہی": "rahi", "رہے": "rahe",
    "رہتا": "rehta", "رہتی": "rehti", "رہتے": "rehte", "رہتیں": "rehtin",
    "رہو": "reho", "رہیں": "rahein",
    "رہ گیا": "reh gaya", "رہ گئی": "reh gai",
    "رہ جاتا": "reh jata", "رہ جاتی": "reh jati",

    # Verb Root: دیکھ (dekh/see)
    "دیکھنا": "dekhna", "دیکھا": "dekha", "دیکھی": "dekhi",
    "دیکھے": "dekhe", "دیکھتا": "dekhta", "دیکھتی": "dekhti",
    "دیکھتے": "dekhte", "دیکھو": "dekho", "دیکھیں": "dekhein",

    # Verb Root: بتا (bata/tell)
    "بتانا": "batana", "بتایا": "bataya", "بتائی": "batayi",
    "بتائے": "bataye", "بتاتا": "bataata", "بتاتی": "bataati",
    "بتاتے": "bataate", "بتاؤ": "batao", "بتائیں": "batayein",

    # Verb Root: پوچھ (pooch/ask)
    "پوچھنا": "poochna", "پوچھا": "poocha", "پوچھی": "poochi",
    "پوچھے": "pooche", "پوچھتا": "poochta", "پوچھتی": "poochti",
    "پوچھتے": "poochte", "پوچھو": "poocho", "پوچھیں": "poochein",

    # Verb Root: چاہ (chaah/want)
    "چاہنا": "chaahna", "چاہا": "chaaha", "چاہی": "chaahi",
    "چاہے": "chahe", "چاہتا": "chahta", "چاہتی": "chahti",
    "چاہتے": "chahte", "چاہو": "chaaho", "چاہیے": "chahiye",

    # Verb Root: کر (kar/do) - imperative & conjunctive already above
    "کرتا": "karta", "کرتی": "karti", "کرتے": "karte",
    "کرنا": "karna", "کرلینا": "kar lena",
    "کرڈالنا": "kar daalna",
    "کرسکتا": "kar sakta", "کرسکتی": "kar sakti", "کرسکتے": "kar sakte",

    # Additional verb roots
    "لگنا": "lagna", "لگتا": "lagta", "لگتی": "lagti", "لگتے": "lagte",
    "لگا": "laga", "لگی": "lagi", "لگے": "lage",
    "لگانا": "lagana", "لگایا": "lagaya",

    "ملنا": "milna", "ملا": "mila", "ملی": "mili", "ملے": "mile",
    "ملتا": "milta", "ملتی": "milti", "ملتے": "milte",
    "ملو": "milo", "ملیں": "milein",
    "مل گیا": "mil gaya", "مل گئی": "mil gai",

    "چلنا": "chalna", "چلا": "chala", "چلی": "chali", "چلے": "chale",
    "چلتا": "chalta", "چلتی": "chalti", "چلتے": "chalte",
    "چلو": "chalo", "چلیں": "chalein",

    "بیٹھنا": "baithna", "بیٹھا": "baitha", "بیٹھی": "baithi",
    "بیٹھے": "baithe", "بیٹھتا": "baithta", "بیٹھتے": "baithte",

    "کھڑا": "khara", "کھڑی": "khari", "کھڑے": "khare",
    "کھڑا ہونا": "khara hona",

    "سونا": "sona", "سوتا": "sota", "سوتی": "soti", "سوتے": "sote",
    "سو گیا": "so gaya",

    "جاگنا": "jaagna", "جاگا": "jaaga", "جاگی": "jaagi",
    "جاگتا": "jaagta", "جاگتی": "jaagti",

    "کھانا": "khana", "کھاتا": "khata", "کھاتے": "khate",
    "کھایا": "khaya", "کھائی": "khayi",
    "کھا لیا": "kha liya",

    "پینا": "peena", "پیتا": "pita", "پیتی": "piti", "پیتے": "pite",
    "پیا": "piya", "پی": "pi", "پئے": "piye",

    "رونا": "rona", "روتا": "rota", "روتی": "roti", "روتے": "rote",
    "رویا": "roya", "روئی": "roi",

    "ہنسنا": "hansna", "ہنس": "hans", "ہنسا": "hansa",
    "ہنستا": "hansta", "ہنستی": "hansti",

    "پڑھنا": "parhna", "پڑھتا": "parhta", "پڑھتی": "parhti",
    "پڑھا": "parha", "پڑھی": "parhi",
    "پڑھو": "parho", "پڑھیں": "parhein",
    "پڑھ لیا": "parh liya",

    "لکھنا": "likhna", "لکھا": "likha", "لکھی": "likhi",
    "لکھتا": "likhta", "لکھتے": "likhte", "لکھو": "likho",
    "لکھ دیا": "likh diya",

    "سمجھنا": "samajhna", "سمجھا": "samjha", "سمجھی": "samjhi",
    "سمجھتا": "samajhta", "سمجھتی": "samajhti", "سمجھتے": "samajhte",
    "سمجھو": "samjho", "سمجھیں": "samjhein",

    "جاننا": "jaanna", "جانتا": "janta", "جانتے": "jante",
    "جانا": "jaana", "جانتی": "jaanti",
    "جان": "jaan", "جانے": "jaane",

    "آن": "aan", "جا": "jaa",
    "بچ": "bach", "مر": "mar",
    "نکل": "nikal", "گزر": "guzar",
    "پکڑ": "pakar", "چھوڑ": "chhor",
    "بدل": "badal", "بھیج": "bhej",
    "بن": "ban", "بنا": "bana", "بنی": "bani", "بنے": "bane",
    "بانٹ": "baant",
    "اٹھ": "uth", "اٹھا": "utha", "اٹھی": "uthi", "اٹھے": "uthe",
    "اٹھ": "uth",
    "لڑ": "lar", "لڑا": "lara", "لڑی": "lari",
    "جیت": "jeet", "جیتا": "jeeta",
    "ہار": "haar", "ہارا": "hara",
    "ڈال": "daal", "ڈالا": "daala", "ڈالی": "daali",
    "ڈال": "daal",
    "مار": "maar", "مارا": "maara", "ماری": "maari",
    "مار": "maar",
    "توڑ": "tore", "توڑا": "tora",
    "لا": "laa", "لایا": "laya",
    "پا": "paa", "پایا": "paya",

    # Possessives & postpositions
    "کا": "ka", "کی": "ki", "کے": "ke",
    "کو": "ko", "سے": "se", "میں": "mein",
    "پر": "par", "نے": "ne", "والا": "wala",
    "والی": "wali", "والے": "wale", "والی": "wali",
    "کے لیے": "ke liye", "کے لئے": "ke liye",
    "کے باوجود": "ke bawajood",
    "کے بارے میں": "ke bare mein",
    "کے ساتھ": "ke saath",
    "کے بغیر": "ke baghair",
    "کے اندر": "ke andar",
    "کے باہر": "ke bahar",
    "کے اوپر": "ke oopar",
    "کے نیچے": "ke neeche",
    "کے آگے": "ke aage",
    "کے پیچھے": "ke peeche",
    "کے قریب": "ke qareeb",
    "کے دور": "ke door",

    # Common adjectives
    "اچھا": "acha", "اچھی": "achi", "اچھے": "achay",
    "برا": "bura", "بری": "buri", "برے": "bure",
    "بڑا": "bara", "بڑی": "bari", "بڑے": "baray",
    "چھوٹا": "chhota", "چھوٹی": "chhoti", "چھوٹے": "chhotay",
    "نئے": "naye", "نیا": "naya", "نئی": "nayi",
    "پرانا": "purana", "پرانی": "purani", "پرانے": "purane",
    "تازہ": "taza", "نرم": "naram", "سخت": "sakht",
    "کمزور": "kamzor", "طاقتور": "taqatwar",
    "خوش": "khush", "غمگین": "ghamgeen", "اداس": "udaas",
    "تنہا": "tanha", "اکیلا": "akela", "اکیلی": "akeli",
    "بیمار": "bimar", "صحت مند": "sehat mand",
    "امیر": "ameer", "غریب": "ghareeb",
    "لمبا": "lamba", "لمبی": "lambi", "لمبے": "lambe",
    "چوڑا": "chora", "چوڑی": "chori",
    "موٹا": "mota", "پتلا": "patla",
    "گہرا": "ghera", "گہری": "gehri", "گہرے": "gehre",
    "ہلکا": "halka", "ہلکی": "halki",
    "بھاری": "bhaari", "بھاری": "bhaari",
    "سست": "sust", "تیز": "tez",
    "صاف": "saaf", "گندا": "ganda", "گندی": "gandi",
    "میٹھا": "meetha", "کڑوا": "karwa",
    "قریب": "qareeb", "دور": "door",
    "ممکن": "mumkin", "ناممکن": "namumkin",
    "ضروری": "zaroori", "غیر ضروری": "ghair zaroori",
    "صرف": "sirf", "محض": "mehez",
    "بہت": "bahut", "بہت زیادہ": "bahut zyada",
    "تھوڑا": "thoda", "تھوڑی": "thodi", "تھوڑے": "thodai",
    "زیادہ": "zyada", "کافی": "kaafi",
    "کم": "kam", "بے حد": "be-hadd",
    "انتہائی": "intehai", "نہایت": "nihayat",
    "بہتر": "behtar", "بدتر": "badtar",
    "آسان": "aasaan", "مشکل": "mushkil",
    "مہنگا": "mehnga", "سستا": "sasta",
    "خوبصورت": "khubsurat", "بدصورت": "badsurat",
    "حسین": "haseen", "وحشی": "weheshi",
    "نیک": "nek", "بد": "bad",
    "سچ": "sach", "جھوٹا": "jhoota", "جھوٹی": "jhooti",
    "پاگل": "paagal", "دیوانہ": "deewana",

    # Body parts
    "سر": "sar", "بال": "baal", "آنکھ": "aankh", "آنکھیں": "aankhein",
    "آنکھوں": "aankhon", "کان": "kaan", "ناک": "naak",
    "منہ": "munh", "ہونٹ": "hont", "ہونٹھ": "honth",
    "دان٘ت": "daant", "زبان": "zaban",
    "گردن": "gardan", "کندھا": "kandha", "کندھے": "kandhay",
    "ہاتھ": "haath", "ہاتھوں": "haathon", "بازو": "baazu",
    "انگلی": "ungli", "انگلیاں": "ungliyan",
    "پاؤں": "paaon", "پیر": "pair",
    "جسم": "jism", "بدن": "badn",
    "دل": "dil", "دھڑکن": "dhadkan",
    "چہرہ": "chehra", "چہرے": "chehre",
    "پیشانی": "peshani", "ٹھوڑی": "thori",

    # Nature
    "پانی": "paani", "بارش": "baarish", "بادل": "baadal",
    "بجلی": "bijli", "گرج": "garaj",
    "سورج": "suraj", "چاند": "chaand", "ستارہ": "sitarah",
    "آسمان": "aasman", "زمین": "zameen",
    "ہوا": "hawa", "آگ": "aag", "دھواں": "dhuan",
    "پہاڑ": "pahad", "سمندر": "samandar",
    "دریا": "darya", "ندی": "nadi", "نہر": "nehr",
    "پھول": "phool", "پتہ": "patta", "پتے": "pattay",
    "درخت": "darakht", "جنگل": "jangal",
    "میدان": "maidan", "صحرا": "sahra",
    "آندھی": "aandhi", "طوفان": "toofan",

    # Places
    "گھر": "ghar", "مکان": "makaan",
    "کمرہ": "kamra", "کمرے": "kamray",
    "دروازہ": "darwaza", "دروازے": "darwazay",
    "کھڑکی": "khirki", "دیوار": "deewar",
    "چھت": "chhat", "فرش": "farsh",
    "سیڑھی": "seerhi", "سیڑھیاں": "seerhiyan",
    "باتھ روم": "bathroom", "باورچی خانہ": "bawarchi khana",
    "بستے": "baste", "بستر": "bistar",
    "صوفہ": "sofa", "میز": "meez", "کرسی": "kursi",
    "الماری": "almari", "الماری": "almari",
    "کتاب": "kitab", "کتابیں": "kitabein", "کتابوں": "kitabon",
    "قلم": "qalam", "کاغذ": "kaghaz",
    "شہر": "sheher", "گاؤں": "gaon", "دیہات": "dehaat",
    "سڑک": "sarak", "گلی": "gali", "راہ": "raah",
    "چوراہا": "chauraha",
    "ملک": "mulk", "دارالحکومت": "dar-ul-hukumat",
    "مسجد": "masjid", "مندر": "mandir", "گرجا": "girja",
    "اسکول": "school", "مدرسہ": "madrasa",
    "دوکان": "dukan", "بازار": "bazaar",
    "ہسپتال": "hospital", "ڈاکٹر": "doctor",

    # Relationships
    "ماں": "maan", "باپ": "baap",
    "مाँ": "maan", "ابو": "abbu", "امّی": "ammi",
    "اماں": "amaan", "ابا": "abba",
    "بیٹا": "beta", "بیٹی": "beti",
    "بھائی": "bhai", "بہن": "behen",
    "بہنیں": "behnein",
    "چچا": "chacha", "چچی": "chachi",
    "ماموں": "mamoon", "ممانی": "mumani",
    "خالہ": "khala", "خالو": "khaloo",
    "نانا": "nana", "نانی": "nani",
    "دادا": "dada", "دادی": "dadi",
    "پوتا": "pota", "پوتی": "poti",
    "شوہر": "shohar", "بیوی": "biwi",
    "بیگم": "begum", "صاحب": "sahab",
    "دوست": "dost", "دوستوں": "doston",
    "دشمن": "dushman",
    "پڑوسی": "padosi", "پڑوسی": "padosi",
    "استاد": "ustad", "شاگرد": "shagird",
    "ملازم": "mulazim", "آقا": "aaka",
    "راجہ": "raja", "رانی": "rani",
    "بادشاہ": "badshah", "وزیر": "wazir",

    # Emotions & states
    "محبت": "mohabbat", "پیار": "pyar", "عشق": "ishq",
    "نفرت": "nafrat", "غصہ": "ghussa", "غصّہ": "ghussa",
    "خوشی": "khushi", "غم": "gham", "اداسی": "udaasi",
    "تنہائی": "tanhai",
    "درد": "dard", "تکلیف": "takleef", "آنسو": "aansoo",
    "آنسوؤں": "aanson",
    "مسکراہٹ": "muskurahat", "ہنسی": "hansi",
    "خوف": "khauf", "ڈر": "dar",
    "حوصلہ": "hausla", "ہمت": "himmat",
    "بے چینی": "bechaini", "بے صبری": "be-sabri",
    "شوق": "shauq", "ارمان": "arman",
    "آرزو": "aarzoo", "خواہش": "khwahish",
    "امید": "umeed", "ناامیدی": "na-umeedi",
    "یقین": "yaqeen", "شک": "shak",
    "ایمان": "imaan", "صبر": "sabr",
    "سکون": "sukoon", "پریشانی": "pareshani",
    "حیرت": "hairat", "تعجب": "taajjub",
    "شرمندگی": "sharmindagi",
    "جذبات": "jazbaat", "احساس": "ehsaas",
    "خیال": "khayal", "خیالات": "khayalaat",
    "سوچ": "soch", "فکر": "fikr",
    "یاد": "yaad", "یادیں": "yaadein", "یادوں": "yadon",

    # Abstract concepts
    "زندگی": "zindagi", "موت": "maut", "مرنا": "marna",
    "دنیا": "duniya", "آخرت": "aakhirat",
    "وقت": "waqt", "زمانہ": "zamana", "دور": "daur",
    "بات": "baat", "باتیں": "baatein",
    "کام": "kaam",
    "طریقہ": "tareeqa", "طور": "tore",
    "طرح": "tarah", "طرح طرح": "tarah tarah",
    "قسم": "qism", "قسمت": "qismat",
    "بھروسہ": "bharosa", "اعتبار": "etbaar",
    "سچ": "sach", "حق": "haq",
    "جھوٹ": "jhoot", "فریب": "fareb",
    "طاقت": "taqat", "زور": "zor",
    "نظم": "nazm", "ترتیب": "tarteeb",
    "روشنی": "roshni", "اندھیرا": "andhera",
    "آواز": "aawaz", "آوازیں": "aawazein",
    "خاموشی": "khamoshi",
    "مشکل": "mushkil", "آسانی": "aasani",
    "فائدہ": "faida", "نقصان": "nuqsan",
    "قاعدہ": "qayda",
    "دلیل": "daleel", "ثبوت": "saboot",
    "انصاف": "insaaf", "ظلم": "zulam",
    "آزادی": "azadi", "قید": "qaid",
    "جنت": "jannat", "دوزخ": "dozakh",

    # Conjunctions & connectors
    "اور": "aur", "لیکن": "lekin", "مگر": "magar",
    "کیونکہ": "kyunke", "چونکہ": "chunke",
    "تاکہ": "take", "کہ": "ke",
    "اگر": "agar", "اگرچہ": "agarche",
    "حالانکہ": "halanke", "جبکہ": "jabke",
    "جب تک": "jab tak", "جب بھی": "jab bhi",
    "تب بھی": "tab bhi",
    "پھر بھی": "phir bhi", "اس لیے": "is liye",
    "اس لئے": "is liye", "اسی لیے": "isi liye",
    "اسی لئے": "isi liye",
    "تاہم": "taham", "بلکہ": "balke",
    "سوائے": "siwaye", "علاوہ": "ilawa",
    "بجائے": "bajaye", "بشرطیکہ": "basharteke",
    "یعنی": "yani", "مثلاً": "masalan",
    "فی الحقیقت": "filhaqiqat",
    "بہرحال": "bahar-haal",
    "جیسے": "jaise", "ویسے": "waise",
    "ابھی": "abhi", "فی الحال": "filhaal",

    # Numerals (Urdu words for numbers)
    "ایک": "ek", "دو": "do", "تین": "teen", "چار": "chaar",
    "پانچ": "paanch", "چھ": "chhah", "سات": "saat",
    "آٹھ": "aath", "نو": "nau", "دس": "das",
    "گیارہ": "gyarah", "بارہ": "barah", "تیرہ": "terah",
    "چودہ": "chaudah", "پندرہ": "pandrah",
    "سولہ": "solah", "سترہ": "satrah", "اٹھارہ": "atharah",
    "انیس": "unees", "بیس": "bees",
    "تیس": "tees", "چالیس": "chalees", "پچاس": "pachas",
    "ساٹھ": "saath", "ستّر": "sattar", "اسی": "asi",
    "نوّے": "naway", "سو": "so",
    "ہزار": "hazaar", "لاکھ": "laakh", "کروڑ": "karor",
    "ارب": "arab",
    "پہلا": "pehla", "پہلی": "pehli", "دوسرا": "doosra",
    "دوسری": "doosri", "تیسرا": "teesra", "تیسری": "teesri",

    # Arabic/Islamic words
    "اللہ": "Allah", "خدا": "Khuda",
    "نماز": "namaz", "روزہ": "roza", "حج": "hajj",
    "زکوٰۃ": "zakat",
    "دعا": "dua", "دعائیں": "duaein",
    "مسجد": "masjid", "مولانا": "maulana",
    "قرآن": "Quran", "حدیث": "hadees",
    "سلام": "salam", "وعلیکم": "walaikum",
    "بسم اللہ": "Bismillah",
    "الحمد اللہ": "Alhamdulillah",
    "ان شاء اللہ": "InshaAllah",
    "ماشاء اللہ": "MashaAllah",
    "سبحان اللہ": "SubhanAllah",
    "اللہ اکبر": "Allahu Akbar",
    "استغفر اللہ": "Astaghfirullah",
    "جزاک اللہ": "JazakAllah",

    # Literary words
    "شاعری": "shaayari", "شاعر": "shaayar", "شعر": "sher",
    "غزل": "ghazal", "نظم": "nazm", "مرثیہ": "marsiya",
    "رباعی": "rubai", "قطعہ": "qita",
    "تشبیہ": "tashbeeh", "استعارہ": "istaara",
    "قافیہ": "qafiya", "ردیف": "radeef",
    "بحر": "behr", "وزن": "wazn",
    "محفل": "mehfil", "مشاعرہ": "mushaira",

    # Colors
    "سفید": "safed", "سیاہ": "siyah",
    "کالا": "kala", "کالی": "kali", "کیلے": "kelay",
    "لال": "laal", "نیلا": "neela", "نیلی": "neeli",
    "پیلا": "peela", "پیلی": "peeli",
    "سبز": "sabz", "سبزی": "sabzi",
    "نارنجی": "narangi", "جامنی": "jamni",
    "سنہرا": "sunhera", "سنہری": "sunheri",
    "چاندی": "chaandi", "سونے": "sonay",

    # Common nouns (extra)
    "انسان": "insaan", "آدمی": "aadmi", "عورت": "aurat",
    "بچہ": "bachcha", "بچے": "bachchay", "بچی": "bachchi",
    "لڑکا": "larka", "لڑکی": "larki", "لڑکے": "larkay",
    "نوجوان": "naujawan", "جوان": "jawan",
    "بوڑھا": "boorha", "بوڑھی": "boorhi",
    "امیر": "ameer", "غریب": "ghareeb",
    "بادشاہ": "badshah", "غلام": "ghulam",
    "ملک": "mulk", "دیس": "des",
    "دھن": "dhan", "دولت": "dolat",
    "خزانہ": "khazana",
    "خبر": "khabar", "خبریں": "khabrein",
    "بات چیت": "baat cheet",
    "شور": "shore", "غل": "ghul",
    "خوشبو": "khushbu", "مہک": "mahak",
    "ذائقہ": "zaiqa",
    "آگ": "aag", "شعلہ": "shola",
    "لو": "loo", "گرمی": "garmi", "سردی": "sardi",
    "چادر": "chaadar", "کمبل": "kambal",
    "تلوار": "talwar", "بندوق": "bandook",
    "گولی": "goli", "چھری": "chhuri",
    "کپ": "cup", "پلیٹ": "plate",
    "چمچ": "chammach", "چمچہ": "chammach",
    "چاقو": "chaqoo", "کانٹا": "kanta",

    # Urdu-specific constructs
    "بے": "be", "با": "ba", "لا": "la",
    "غیر": "ghair", "نے": "ne", "سے": "se",
    "ہی": "hi", "بھی": "bhi", "ہی": "hi",
    "تو": "toh", "نہ": "na",
    "بس": "bas", "صرف": "sirf",
    "بہت": "bahut", "بھی": "bhi",
    "اوہ": "oh", "آہ": "aah",
    "ہائے": "haye", "افسوس": "afsos",
    "شاباش": "shabash", "واہ": "wah",
    "مبارک": "mubarak",
    "شکریہ": "shukriya",
    "معاف": "maaf", "معذرت": "mazrat",
    "برائے مہربانی": "barae meharbani",
    "خدا حافظ": "Khuda Hafiz",
    "الوداع": "alwida",
    "آمین": "aameen",

    # Extra common words from fiction
    "لاش": "laash", "لاشیں": "lashein",
    "خون": "khoon", "لہو": "lahoo",
    "چیخ": "cheekh", "چیخیں": "cheekhein",
    "چِلّانا": "chillana",
    "دھماکہ": "dhamaka",
    "آگ": "aag",
    "بم": "bomb",
    "بندوق": "bandook", "گولی": "goli",
    "ٹکٹ": "ticket",
    "فون": "phone", "موبائل": "mobile",
    "کمپیوٹر": "computer",
    "گاڑی": "gaari", "گاڑیاں": "gaariyan",
    "کار": "car",
    "بس": "bus",
    "ٹرک": "truck",
    "ہوائی جہاز": "hawai jahaz",
    "جہاز": "jahaz",
    "کپتان": "captain",
    "ڈرائیور": "driver",
    "ڈاکٹر": "doctor",
    "وکیل": "vakeel",
    "جج": "judge",
    "پولیس": "police",
    "چور": "chor", "ڈاکو": "daku",
    "جیل": "jail",
    "عدالت": "adalat",
    "قانون": "qanoon",
    "جرمانہ": "jurmana",
    "گواہ": "gawah",
    "ثبوت": "saboot",
    "کیس": "case",
    "مقدمہ": "muqadma",
    "فیصلہ": "faisla",
    "سزا": "saza",
    "بری": "bari",
    "مجرم": "mujrim",
    "بے گناہ": "be-gunah",
    "صاحب": "sahab",
    "حضور": "huzoor",
    "جناب": "janab",
    "محترم": "muhtaram",
    "محترمہ": "muhtarama",
    "صدر": "sadar",
    "وزیر اعظم": "wazir-e-azam",
    "سیاست": "siyasat",
    "سیاستدان": "siyasatdan",
    "انتخاب": "intikhab",
    "ووٹ": "vote",
    "جمہوریت": "jamhuriyat",
    "حکومت": "hukumat",
    "سرکار": "sarkar",
    "دفتر": "daftar",
    "دفاتر": "dafatir",
    "فائل": "file",
    "دستاویز": "dastavez",
    "خط": "khat", "خطوط": "khutoot",
    "کاغذ": "kaghaz", "اخبار": "akhbar",
    "جریدہ": "jarida",
    "مضمون": "mazmoon",
    "تحریر": "tehreer",
    "قلم": "qalam",
    "روشنائی": "roshnai",
    "صفحہ": "safha",
    "پرچہ": "parcha",
    "لفظ": "lafz", "الفاظ": "alfaz",
    "جملہ": "jumla",
    "زبان": "zaban", "بول": "bol",
    "بات چیت": "baat cheet",
    "گفتگو": "guftugu",
    "ملاقات": "mulaqaat",
    "اجلاس": "ijlaas",
    "میٹنگ": "meeting",
    "کانفرنس": "conference",
    "ٹیلیفون": "telephone",
    "پیغام": "paigham",
    "سوال": "sawal", "جواب": "jawab",
    "سوالات": "sawalaat",
    "پوچھ": "poochh",
    "پوچھ گچھ": "poochh gachh",
    "پتہ": "pata", "پتے": "patay",
    "نشان": "nishaan",
    "علامت": "alamat",
    "نشاندہی": "nishandahi",

    # Common day-to-day words
    "چائے": "chai", "قہوہ": "qehwa",
    "دودھ": "doodh", "شکر": "shakar",
    "نمک": "namak", "روٹی": "roti", "نان": "naan",
    "سبزی": "sabzi", "گوشت": "gosht",
    "چاول": "chawal", "دال": "daal",
    "پانی": "paani", "برف": "baraf",
    "آگ": "aag", "لکڑی": "lakri",
    "کوئلہ": "koyla",
    "بجلی": "bijli",
    "تار": "taar",
    "روپیہ": "rupya", "پیسہ": "paisa", "پیسے": "paisay",
    "نوٹ": "note", "کاغذی نوٹ": "kaghzi note",
    "سکہ": "sikka",
    "بوری": "bori", "تھیلا": "thaila",
    "تالا": "tala", "چابی": "chabi",
    "تکیہ": "takiya", "گدا": "gadda",
    "چادر": "chaadar",
    "لحاف": "lihaaf",
    "بستر": "bistar",
    "صندوق": "sandooq", "پیٹی": "peti",
    "تھیلا": "thaila",
    "ٹوپی": "topi",
    "جوتا": "joota", "جوتے": "jootay",
    "موزہ": "moza",
    "جراب": "jurab",
    "شرٹ": "shirt", "پتلون": "patloon",
    "کوٹ": "coat", "واسکٹ": "waistcoat",
    "دوپٹہ": "dupatta",
    "برقع": "burqa",
    "احرام": "ehraam",
    "عمامہ": "ammama",
    "کرتا": "kurta", "شلوار": "shalwar",
    "پائجامہ": "pajama",

    # Missing words from ch-01 analysis
    "چھو": "chhu", "چھو نہیں": "chhu nahin",
    "لیٹا": "leta", "لیٹی": "leti", "لیٹے": "lete",
    "اٹرنے": "utarnay", "اتر": "utar",
    "پچھلا": "pichla", "پچھلے": "pichlay", "پچھلی": "pichli",
    "پچھلے سال": "pichlay saal",
    "دراڑ": "daraar", "دراڑیں": "daraarein",
    "دراڑ": "daraar",
    "کھلا": "khula", "کھلی": "khuli", "کھلے": "khulay",
    "کھلنا": "khulna", "کھل": "khul",
    "دیکھ": "dekh", "دیکھو": "dekho", "دیکھیں": "dekhein",
    "دیکھ کر": "dekh kar",
    "گہرا": "ghera", "گہرائی": "gerai", "گہرے": "ghere",
    "زیادہ": "zyada", "زیادہ تر": "zyada tar",
    "جگہ": "jagah", "جگہوں": "jagahon",
    "پہچان": "pehchan",
    "شکل": "shakl", "شکلیں": "shaklein",
    "ممکن": "mumkin", "ناممکن": "namumkin",
    "زاویہ": "zawya", "زاویے": "zawaye",
    "لے لیا": "le liya", "لے": "le",
    "بج": "baj", "بجے": "bajay", "بج رہے": "baj rahay",
    "تین": "teen", "تین بج": "teen baj",
    "جاگ": "jaag", "جاگی": "jaagi", "جاگو": "jaago",
    "نیند": "neend",
    "انگلی": "ungli", "انگلیاں": "ungliyan",
    "چہرہ": "chehra", "چہرے": "chehray",
    "چھت": "chhat",
    "کمرہ": "kamra", "کمروں": "kammon",
    "دھوپ": "dhoop",
    "سادہ": "sada", "سادگی": "sadgi",
    "مصروف": "masroof",
    "کمپیوٹر": "computer",
    "فائل": "file",
    "کی بورڈ": "keyboard",
    "ماؤس": "mouse",
    "اسکرین": "screen",
    "اسکرین": "screen",
    "بجلی": "bijli",
    "چل": "chal",
    "چل": "chal",
    "بتا": "bata", "بتاؤ": "batao",
    "سکڑ": "sikar",
    "گاڑی": "gaari", "گاڑی": "gaari",
    "دھماکہ": "dhamaka",
    "ٹھنڈا": "thanda", "ٹھنڈی": "thandi",
    "پیاس": "pyas",
    "بھوک": "bhook",
    "ہنسنا": "hansna",
    "چلانا": "chilana",
    "مسکرانا": "muskurana",
    "دھکا": "dhakka",
    "چوٹ": "chot",
    "ٹھیک": "theek",
    "بس": "bas",
    "پوچھ": "poochh",
    "کھانا": "khana",
    "کھا": "kha",
    "پانی": "paani",
    "جواب": "jawab",
    "سوال": "sawal",
    "پتا": "pata", "پتہ": "pata", "پتا نہیں": "pata nahin",
    "معلوم": "maloom",
    "ساتھ": "saath",
    "کہ": "ke", "کِہ": "ke",
    "یاد": "yaad",
    "مگر": "magar",
    "چاہیے": "chahiye", "چاہئے": "chahiye",
    "شاید": "shayad",
    "ضرور": "zaroor",
    "خوش": "khush",
    "تھک": "thak",
    "دکھ": "dukh",
    "سکھ": "sukh",
    "جھوٹ": "jhoot",
    "سچ": "sach",

    # More corrections from chapters
    "گزر": "guzar", "گزرنا": "guzarna", "گزرا": "guzara",
    "گزر گیا": "guzar gaya",
    "چھوڑا": "chhora", "چھوڑی": "chhori", "چھوڑے": "chhoray",
    "چھوڑ": "chhor",
    "پردہ": "parda", "پردے": "parday", "پردوں": "pardon",
    "کھنچ": "khinach", "کھنچے": "khinchay",
    "آتی": "aati", "آتے": "aate", "آتا": "aata",
    "چارج": "charge", "چارجنگ": "charging",
    "اتار": "utaar", "اتارا": "utaara", "اتاری": "utaari",
    "اتار": "utaar",
    "دوسرا": "doosra", "دوسری": "doosri", "دوسرے": "doosray",
    "تیسرا": "teesra", "تیسری": "teesri", "تیسرے": "teesray",
    "دھیما": "dheema", "دھیمی": "dheemi",
    "دھیرے": "dheeray", "دھیرے دھیرے": "dheeray dheeray",
    "گہرائی": "gherai",
    "آنکھ": "aankh", "آنکھیں": "aankhein", "آنکھوں": "aankhon",
    "کیلنڈر": "calendar",
    "ڈائری": "diary",
    "نوٹ بک": "notebook",
    "چابی": "chaabi", "چابیاں": "chaabiyan",
    "تالا": "taala",
    "سیل": "cell",
    "بیٹری": "battery",
    "سگنل": "signal",
    "نیٹ ورک": "network",
    "انٹرنیٹ": "internet",
    "وائس": "voice",
    "میسج": "message",
    "میل": "mail",
    "ای میل": "email",
    "ان باکس": "inbox",
    "ڈیلیٹ": "delete",
    "سیو": "save",
    "پرنٹ": "print",
    "اسکین": "scan",
    "اپ ڈیٹ": "update",
    "ڈاؤن لوڈ": "download",
    "اپ لوڈ": "upload",
    "شئیر": "share",
    "لائک": "like",
    "کمنٹ": "comment",
    "پروفائل": "profile",
    "وال پیپر": "wallpaper",
    "گیم": "game",
    "گانا": "gana", "گیت": "geet",
    "فلم": "film",
    "ڈرامہ": "drama",
    "نظر": "nazar",
    "جلوہ": "jalwa",
    "خواب": "khwab",
    "خوابوں": "khwabon",
    "تعریف": "tareef",
    "تنقید": "tanqeed",
    "تاریخ": "tareekh",
    "جغرافیہ": "jughrafia",
    "سائنس": "science",
    "ریاضی": "riyazi",
    "ادب": "adab",
    "شاعری": "shayari",
    "موسیقی": "mausiqi",
    "مصور": "musawar",
    "آرٹ": "art",
    "رنگ": "rang",
    "رنگوں": "rangon",
    "انگ": "ang",
    "اعضا": "aza",
    "ہڈی": "haddi",
    "پٹھہ": "pata",
    "نڈی": "nas",
    "خون": "khoon",
    "نبض": "nabz",
    "سانس": "saans",
    "سانسیں": "saansein",
    "سیخ": "seekh",
    "چاقو": "chaqoo",
    "تلوار": "talwar",
    "برچھی": "barchhi",
    "ڈھال": "dhaal",
    "ہیلمٹ": "helmet",
    "زرہ": "zarah",
    "آئینہ": "aaina",
    "شیشہ": "sheesha",
    "کانچ": "kaanch",
    "پتھر": "patthar",
    "چٹان": "chattan",
    "ریت": "rait",
    "مٹی": "mitti",
    "دھول": "dhool",
    "دھواں": "dhuan",
    "لال": "laal", "لیلی": "laili",
    "نڑ": "nar",
    "مادہ": "mada",
    "نر": "nar",
}


def char_transliterate(word):
    """Character-level fallback with vowel insertion rules."""
    if not word:
        return ""

    result = []
    i = 0
    while i < len(word):
        ch = word[i]

        # Zero-width non-joiner
        if ch in ('\u200c', '\u200d', '\u200b'):
            i += 1
            continue

        # Skip punctuation-like characters inside word
        if ch in ('،', '۔', '؟', '،', '!', '?', '.', ',', ';', ':', '-'):
            result.append(ch)
            i += 1
            continue

        if ch in CHAR_MAP:
            c = CHAR_MAP[ch]
            prev_ch = word[i - 1] if i > 0 else None
            next_ch = word[i + 1] if i + 1 < len(word) else None

            # Waw rules: consonant w vs vowel o/u
            if ch == 'و':
                if next_ch is None:
                    c = 'o'
                elif i == 0:
                    c = 'w'
                elif not is_consonant(next_ch):
                    c = 'w'
                else:
                    # Between consonants - decide based on context
                    if prev_ch and is_consonant(prev_ch):
                        c = 'o'
                    else:
                        c = 'w'

            # Chhoti ye rules: vowel i vs consonant y
            elif ch == 'ی':
                if next_ch is None:
                    c = 'i'
                elif i == 0:
                    c = 'y'
                elif not is_consonant(next_ch):
                    c = 'y'
                else:
                    c = 'i'

            # Alif rules
            elif ch == 'ا':
                if next_ch is None:
                    c = 'a'
                elif next_ch == 'ی':
                    c = 'a'
                elif i == 0:
                    c = 'a'
                elif not is_consonant(next_ch):
                    c = ''
                else:
                    c = 'a'

            # Heh rules (word-final ha sound)
            elif ch == 'ہ' and next_ch is None:
                c = 'a'
            elif ch == 'ہ' and next_ch and not is_consonant(next_ch):
                c = 'h'

            result.append(c)
        else:
            result.append(ch)

        i += 1

    # Insert vowels between consonant clusters for readability
    return insert_vowels(''.join(result))


def is_consonant(ch):
    """Check if a Unicode character is an Urdu consonant."""
    c = ord(ch)
    if 0x0628 <= c <= 0x06CC:
        # Exclude diacritics and vowel letters
        not_consonant = {0x0627, 0x0622, 0x0648, 0x064A, 0x06CC, 0x06D2,
                         0x064B, 0x064C, 0x064D, 0x064E, 0x064F, 0x0650,
                         0x0651, 0x0652, 0x0670, 0x06E0, 0x06E1, 0x06E2,
                         0x06E3, 0x06E4, 0x06E5, 0x06E6, 0x06E7, 0x06E8,
                         0x0648}  # Waw is a vowel letter
        return c not in not_consonant
    # Also treat ۂ (0x06C2), ہ (0x06C1), ھ (0x06BE) as consonants
    if c in (0x06C1, 0x06BE, 0x06C2, 0x0621):
        return True
    return False


def insert_vowels(text):
    """Insert 'a' between consecutive consonants for readability."""
    # Don't insert for certain consonant pairs that are pronounced together
    skip_pairs = {
        'sh', 'kh', 'gh', 'zh', 'ch', 'th', 'dh', 'ph', 'bh',
        'rh', 'lh', 'nh', 'mh', 'nh',
        'tr', 'dr', 'kr', 'gr', 'pr', 'br', 'fr',
        'kl', 'pl', 'bl', 'gl', 'fl',
        'ks', 'ps', 'ts',
        'st', 'sp', 'sk', 'sm', 'sn', 'sl', 'sw',
        'nd', 'nt', 'nk', 'ng', 'ntr', 'ndr',
        'ct', 'pt', 'kt',
        'mp', 'mb',
        'x', 'z',
    }
    result = []
    i = 0
    while i < len(text):
        result.append(text[i])
        # Check if current char is a consonant and next is also a consonant
        if i + 1 < len(text):
            cur = text[i].lower()
            nxt = text[i + 1].lower()
            pair = cur + nxt
            triple = cur + nxt + (text[i + 2].lower() if i + 2 < len(text) else '')
            if (cur.isalpha() and nxt.isalpha()
                    and cur not in 'aeiou'
                    and nxt not in 'aeiou'
                    and pair not in skip_pairs
                    and triple[:-1] not in skip_pairs):
                result.append('a')
        i += 1
    return ''.join(result)


# ─── Character mapping ───
CHAR_MAP = {
    'ا': 'a', 'آ': 'aa', 'ب': 'b', 'پ': 'p', 'ت': 't', 'ٹ': 't',
    'ث': 's', 'ج': 'j', 'چ': 'ch', 'ح': 'h', 'خ': 'kh', 'د': 'd',
    'ڈ': 'd', 'ذ': 'z', 'ر': 'r', 'ڑ': 'r', 'ز': 'z', 'ژ': 'zh',
    'س': 's', 'ش': 'sh', 'ص': 's', 'ض': 'z', 'ط': 't', 'ظ': 'z',
    'ع': 'a', 'غ': 'gh', 'ف': 'f', 'ق': 'q', 'ك': 'k', 'ک': 'k',
    'گ': 'g', 'ل': 'l', 'م': 'm', 'ن': 'n', 'ں': 'n',     'و': 'o',
    'ہ': 'h', 'ھ': 'h', 'ء': '', 'ی': 'y', 'ے': 'e',
    'ۂ': 'ha', 'ۃ': 'h', 'ٔ': '',
    # Digits
    '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
    '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
}

# Urdu punctuation
PUNCTUATION = set('،۔؟!؛''""''()[]{}«»—–…\t ')


def is_urdu(text):
    """Check if text contains Urdu characters."""
    for ch in text:
        if 0x0600 <= ord(ch) <= 0x06FF:
            return True
    return False


def transliterate_line(line):
    """Transliterate a line of Urdu text to Roman Urdu."""
    line = line.replace('،', ',').replace('۔', '.').replace('؟', '?')
    line = line.replace('؛', ';').replace('«', '"').replace('»', '"')
    line = line.replace('\u200c', '').replace('\u200d', '')

    if not is_urdu(line):
        return line

    tokens = []
    current = []
    for ch in line:
        if ch.isspace() or ch in PUNCTUATION or ch in '.,;:!?()-""\'':
            if current:
                tokens.append(''.join(current))
                current = []
            tokens.append(ch)
        else:
            current.append(ch)
    if current:
        tokens.append(''.join(current))

    result = []
    for token in tokens:
        if not token.strip() or not is_urdu(token):
            result.append(token)
            continue

        if token in WORD_MAP:
            result.append(WORD_MAP[token])
            continue

        # Handle common suffix patterns
        stripped = token
        suffix = ''
        endings = [
            ('وں', 'on'), ('یں', 'ein'), ('ۂ', 'e'),
            ('ات', 'aat'), ('یک', 'ik'),
            ('یت', 'iyat'), ('ئی', 'i'),
            ('اۓ', 'e'), ('ے', 'ay'),
        ]
        for ending, repl in endings:
            if stripped.endswith(ending):
                suffix = repl
                stripped = stripped[:-len(ending)]
                break

        if stripped and stripped in WORD_MAP:
            result.append(WORD_MAP[stripped] + suffix)
            continue

        # Word-internal substring matching (try removing prefixes)
        prefixes = ['بے', 'با', 'لا', 'غیر', 'نہ', 'نا', 'ب', 'ن']
        matched = False
        for prefix in prefixes:
            if token.startswith(prefix) and len(token) > len(prefix):
                rest = token[len(prefix):]
                if rest in WORD_MAP:
                    p_roman = WORD_MAP.get(prefix, char_transliterate(prefix))
                    result.append(p_roman + '-' + WORD_MAP[rest])
                    matched = True
                    break
        if matched:
            continue

        result.append(char_transliterate(token))

    return ''.join(result)


def process_chapter(content, fname):
    """Split front matter, transliterate body + title."""
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            front_matter = '---' + parts[1] + '---'
            body = parts[2]
        else:
            front_matter = ''
            body = content
    else:
        front_matter = ''
        body = content

    if front_matter:
        m = re.search(r'^title:\s*"(.*)"', front_matter, re.MULTILINE)
        if m:
            orig = m.group(1)
            if is_urdu(orig):
                roman = transliterate_line(orig)
                front_matter = front_matter.replace(f'title: "{orig}"', f'title: "{roman}"')

    lines = body.split('\n')
    roman_lines = []
    for line in lines:
        s = line.strip()
        if s.startswith('{{') and '}}' in s:
            roman_lines.append(line)
        else:
            roman_lines.append(transliterate_line(line))

    return front_matter, '\n'.join(roman_lines)


def romanize_novel(source_dir, target_dir):
    """Generate Roman Urdu for all chapters in a novel directory."""
    os.makedirs(target_dir, exist_ok=True)
    for fname in sorted(os.listdir(source_dir)):
        if not fname.endswith('.md') or fname == '_index.md':
            continue
        src = os.path.join(source_dir, fname)
        dst = os.path.join(target_dir, fname)
        with open(src, 'r', encoding='utf-8') as f:
            content = f.read()

        front_matter, roman_body = process_chapter(content, fname)

        if front_matter:
            fm_lines = front_matter.split('\n')
            for idx in range(len(fm_lines) - 1, -1, -1):
                if fm_lines[idx].strip() == '---':
                    fm_lines.insert(idx, 'type: roman')
                    break
            front_matter = '\n'.join(fm_lines)

        output = front_matter + '\n' + roman_body
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"  ✓ {fname}")


def main():
    base = os.path.dirname(__file__)
    novels_dir = os.path.join(base, 'content')
    for novel in sorted(os.listdir(novels_dir)):
        if novel == 'references':
            continue
        source = os.path.join(novels_dir, novel)
        target = os.path.join(source, 'roman')
        if not os.path.isdir(source):
            continue
        chs = [f for f in os.listdir(source) if f.startswith('ch-') and f.endswith('.md')]
        if not chs:
            continue
        print(f"\n📖 {novel} ({len(chs)} chapters)")
        romanize_novel(source, target)


if __name__ == '__main__':
    main()
