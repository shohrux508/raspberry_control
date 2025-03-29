#include <LiquidCrystal_I2C.h>
LiquidCrystal_I2C lcd(0x27, 16, 2);  // Инициализация LCD (16×2)

// Массив пинов для 8 реле и 8 кнопок запуска
const int relayPins[8] = {5, 6, 7, 8, 9, 10, 11, 12};
const int startButtons[8] = {3, 4, 13, A0, A1, A2, A3, A4};

// Глобальные переменные для управления процессом
bool startEnabled = false;        // Флаг, разрешающий запуск (устанавливается онлайн-оплатой)
bool isRunning = false;           // Флаг, что процесс запущен
bool isPaused = false;            // Флаг, что процесс поставлен на паузу
int activeRelay = -1;             // Номер активного реле (-1 – ни одно не активно)
String idPart = "";

unsigned long startTime = 0;      // Время начала процесса
unsigned long pausedTime = 0;     // Время, прошедшее до паузы
unsigned long pauseMoment = 0;    // Момент постановки на паузу
unsigned long workDuration = 0;   // Общее время работы процесса (в мс)

// Параметры времени
const unsigned long baseTime = 30000;           // Базовое время работы (30 секунд)
const unsigned long extraTimePerImpulse = 3000;   // Дополнительное время за "импульс" (3 секунды)

// Переменные для обработки кнопок
unsigned long lastButtonPressTime[8] = {0};
const unsigned long buttonDebounceTime = 500;   // Антидребезг кнопок (500 мс)
bool buttonHeld[8] = {false};
unsigned long lastCountdownTime = 0;            // Время последнего обновления обратного отсчёта

// Прототипы функций
void startProcess(int relayIndex);
void stopProcess();
void pauseProcess();
void resumeProcess();
void updateTimer();
void handleStartPress(int buttonIndex);
void checkButtons();
void checkOnlinePayment();

void setup() {
  // Настройка пинов для кнопок и реле
  for (int i = 0; i < 8; i++) {
    pinMode(startButtons[i], INPUT_PULLUP);
    pinMode(relayPins[i], OUTPUT);
    digitalWrite(relayPins[i], LOW);  // Реле выключены (LOW – неактивно)
  }

  Serial.begin(9600);  // Инициализация последовательного порта
  lcd.init();          // Инициализация LCD
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Готово к работе");
  Serial.println("Готово к работе");
}

void loop() {
  checkOnlinePayment();  // Проверяем входящие сообщения об онлайн оплате
  checkButtons();        // Обработка нажатий кнопок

  if (isRunning && !isPaused)
    updateTimer();       // Обновляем обратный отсчёт времени процесса
}

// Функция проверки онлайн оплаты через последовательный порт с получением ID
void checkOnlinePayment() {
  if (Serial.available() > 0) {
    String message = Serial.readStringUntil('\n');
    message.trim();
    if(message.length() == 0) return;

    String paymentCommand;

    // Если в сообщении присутствует запятая, разделяем команду и ID
    int commaIndex = message.indexOf(',');
    if (commaIndex != -1) {
      paymentCommand = message.substring(0, commaIndex);
      idPart = message.substring(commaIndex + 1);
      idPart.trim();
    } else {
      paymentCommand = message;
    }

    // Обработка команды без дополнительных параметров
    if (paymentCommand == "PAYMENT_OK") {
      startEnabled = true;
      workDuration = baseTime;
      if (idPart.length() > 0) {
        // Ожидаем формат "ID:1234123"
        Serial.print("-confirmed,");
        Serial.print(idPart);
        Serial.println(".");
      } else {
        Serial.println("-confirmed.");
      }
      Serial.println("Онлайн оплата успешна. Запуск процесса разрешен.");
    }
    // Обработка команды с дополнительным временем, например "PAYMENT_OK:3"
    else if (paymentCommand.startsWith("PAYMENT_OK:")) {
      int colonIndex = paymentCommand.indexOf(':');
      if (colonIndex != -1) {
        String extraStr = paymentCommand.substring(colonIndex + 1);
        extraStr.trim();
        int extraImpulses = extraStr.toInt();
        startEnabled = true;
        workDuration = baseTime + extraImpulses * extraTimePerImpulse;
        if (idPart.length() > 0) {
          Serial.print("-confirmed:");
          Serial.print(workDuration / 1000);
          Serial.print(",");
          Serial.print(idPart);
          Serial.println(".");
        } else {
          Serial.print("-confirmed:");
          Serial.print(workDuration / 1000);
          Serial.println(".");
        }
        Serial.print("Онлайн оплата успешна. Дополнительное время: ");
        Serial.print(workDuration / 1000);
        Serial.println(" сек.");
      }
    }
    else {
      Serial.print("Непонятное сообщение: ");
      Serial.println(message);
    }
  }
}

void checkButtons() {
  for (int i = 0; i < 8; i++) {
    if (digitalRead(startButtons[i]) == LOW) {  // Если кнопка нажата
      if (!buttonHeld[i] && millis() - lastButtonPressTime[i] > buttonDebounceTime) {
        lastButtonPressTime[i] = millis();
        buttonHeld[i] = true;
        handleStartPress(i);
      }
    }
    else {
      buttonHeld[i] = false;
    }
  }
}

// Обработка нажатия кнопки запуска/паузы/возобновления
void handleStartPress(int buttonIndex) {
  if (!startEnabled) {  // Если онлайн оплата не подтверждена
    Serial.println("-not_confirmed.");
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Оплата не");
    lcd.setCursor(0, 1);
    lcd.print("подтверждена!");
    return;
  }

  // Если процесс уже запущен или поставлен на паузу, обрабатываем только активную кнопку
  if (isRunning || isPaused) {
    if (activeRelay == buttonIndex) {
      if (!isPaused) {  // Если процесс работает, пытаемся поставить его на паузу
        if (millis() - startTime < 3000) {
          Serial.println("Пауза недоступна в первые 3 секунды.");
          lcd.clear();
          lcd.setCursor(0, 0);
          lcd.print("Пауза недоступна");
          lcd.setCursor(0, 1);
          lcd.print("3 сек старт");
          return;
        }
        else {
          pauseProcess();
        }
      }
      else {  // Если процесс на паузе, пытаемся возобновить работу
        if (millis() - pauseMoment < 2000) {
          Serial.println("Нельзя возобновлять, ждите 2 сек после паузы.");
          lcd.clear();
          lcd.setCursor(0, 0);
          lcd.print("Ждите 2 сек после");
          lcd.setCursor(0, 1);
          lcd.print("паузы");
          return;
        }
        else {
          resumeProcess();
        }
      }
    }
    else {
      Serial.println("Другое реле не может быть активировано пока текущее работает!");
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Реле ");
      lcd.print(activeRelay + 1);
      lcd.setCursor(0, 1);
      lcd.print("в работе");
    }
    return;
  }

  // Если процесс не запущен, запускаем его по выбранной кнопке
  startProcess(buttonIndex);
}

void startProcess(int relayIndex) {
  activeRelay = relayIndex;
  isRunning = true;
  isPaused = false;
  startTime = millis();
  digitalWrite(relayPins[relayIndex], HIGH);   // Включаем реле (HIGH – активное состояние)
  Serial.print("-relay"); Serial.print(relayIndex+1);
  Serial.print("on"); Serial.print(workDuration / 1000); Serial.print(",");Serial.print(idPart);Serial.println(".");
  Serial.print("Процесс запущен на реле ");
  Serial.print(relayIndex + 1);
  Serial.print(" с оставшимся временем: ");
  Serial.print(workDuration / 1000);
  Serial.println(" сек");

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Реле ");
  lcd.print(relayIndex + 1);
  lcd.print(" запущено");
  lcd.setCursor(0, 1);
  lcd.print("Время: ");
  lcd.print(workDuration / 1000);
  lcd.print(" сек");

  lastCountdownTime = millis();
}

void pauseProcess() {
  if (activeRelay != -1) {
    digitalWrite(relayPins[activeRelay], LOW);  // Выключаем реле (LOW – неактивно)
    pausedTime = millis() - startTime;
    pauseMoment = millis();
    workDuration -= pausedTime;  // Корректируем оставшееся время
    isPaused = true;
    Serial.print("-relay"); Serial.print(activeRelay+1);
    Serial.print("stop");Serial.print(",");Serial.print(idPart);Serial.println(".");
    Serial.print("Реле ");
    Serial.print(activeRelay + 1);
    Serial.println(" приостановлено");

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Реле ");
    lcd.print(activeRelay + 1);
    lcd.print(" стоп");
    lcd.setCursor(0, 1);
    lcd.print("Пауза");
  }
}

void resumeProcess() {
  if (isPaused) {
    isPaused = false;
    startTime = millis();
    digitalWrite(relayPins[activeRelay], HIGH);  // Включаем реле
    Serial.print("-relay"); Serial.print(activeRelay+1);
    Serial.print("resumed");Serial.print(",");Serial.print(idPart);Serial.println(".");
    Serial.print("Реле ");
    Serial.print(activeRelay + 1);
    Serial.println(" возобновлено");

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Реле ");
    lcd.print(activeRelay + 1);
    lcd.print(" резюм.");
    lcd.setCursor(0, 1);
    lcd.print("Время: ");
    lcd.print(workDuration / 1000);
    lcd.print(" сек");

    lastCountdownTime = millis();
  }
}

void updateTimer() {
  unsigned long elapsedTime = millis() - startTime;
  unsigned long remainingTime = (workDuration > elapsedTime) ? (workDuration - elapsedTime) : 0;

  if (millis() - lastCountdownTime >= 1000) {
    Serial.print("Оставшееся время: ");
    Serial.print(remainingTime / 1000);
    Serial.println(" сек");

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Ост. время:");
    lcd.setCursor(0, 1);
    lcd.print(remainingTime / 1000);
    lcd.print(" сек");

    lastCountdownTime = millis();
  }

  if (remainingTime == 0)
    stopProcess();
}

void stopProcess() {
  if (activeRelay != -1) {
    digitalWrite(relayPins[activeRelay], LOW);  // Выключаем реле
    Serial.print("-relay"); Serial.print(activeRelay+1);
    Serial.print("off");Serial.print(",");Serial.print(idPart);Serial.println(".");
    Serial.print("Реле ");
    Serial.print(activeRelay + 1);
    Serial.println(" выключено");

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Реле ");
    lcd.print(activeRelay + 1);
    lcd.setCursor(0, 1);
    lcd.print("выкл.");
  }
  isRunning = false;
  isPaused = false;
  activeRelay = -1;
  startEnabled = false;
  Serial.println("Процесс завершен.");

  lcd.setCursor(0, 1);
  lcd.print("Завершено");
  String idPart = "";
}

