זהו פרויקט שמדמה מערכת הזרמת וידאו בסגנון YouTube. המערכת כוללת ממשק משתמש שנבנה באמצעות PyQt5, שרת TCP מותאם אישית שמנהל התחברות, הרשמה והעלאת קבצים, שרת Flask שמספק סטרימינג של וידאו, ואבטחה הכוללת הצפנת AES והחלפת מפתחות Diffie-Hellman.

המערכת תומכת בהעלאת וידאו, צפייה בסרטונים, ספירת צפיות, לייקים, דיסלייקים, שמירת מידע על משתמשים, שמירת תיאורי סרטון, תמונות thumbnail ועוד.

Features 

ממשק משתמש מלא הכולל: Login, Signup, Home, Upload, Watch, Settings.

צפייה בסרטונים בתוך רכיב QWebEngineView.

העלאת סרטונים דרך חיבור TCP מוצפן.

הצפנת AES-256 לכל הנתונים בין לקוח לשרת.

החלפת מפתחות Diffie-Hellman בעת החיבור.

המרת וידאו לפורמט WebM באמצעות ffmpeg.

אחסון נתונים בבסיס נתונים SQLite.

תמיכה בלייקים, דיסלייקים, צפיות ונתוני יוצר הסרטון.

תמיכה ב-Thumbnails לסרטונים.

חיפוש סרטונים לפי שם.

Project Structure

YouTube_client.py – צד לקוח, ממשק PyQt5
YouTube_server.py – שרת TCP שמטפל בהרשמה, התחברות, העלאת סרטונים, עדכון נתונים ועוד
YouTube_http_server.py – שרת Flask שמחזיר וידאו ב־HTTP כולל תמיכה ב-Range
תיקייה youtube_c – מכילה את כל קבצי ה־UI (.ui), תמונות ו־icons
תיקייה youtube – מכילה סרטונים שהועלו, קבצי thumbnail ומסד הנתונים data.db
ffmpeg.exe – משמש להמרת סרטונים לפורמט WebM

Installation

יש להתקין את כל התלויות המופיעות בקובץ requirements.txt.
בנוסף, יש לוודא שקובץ ffmpeg.exe נמצא בתיקייה הראשית של הפרויקט כדי לאפשר המרת וידאו.

Running

על מנת להפעיל את המערכת יש להפעיל את שלושת החלקים:

הפעלת שרת ה-TCP:
python YouTube_server.py

הפעלת שרת הסטרימינג:
python YouTube_http_server.py

הפעלת צד הלקוח:
python YouTube_client.py

Requirements

המערכת משתמשת בין היתר בתלויות הבאות:
PyQt5
Flask
flask-cors

(שאר התלויות נמצאות ב־requirements.txt)

License

MIT License
