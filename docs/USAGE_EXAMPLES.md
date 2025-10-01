# Usage Examples

## Basic Usage

### Step 1: Configure Stations (One-time Setup)

```
User: /setstations

Bot: 🚂 Мастер настройки станций
     🏠 Шаг 1: Базовая станция
     
     Давайте настроим вашу базовую станцию (место начала поездки).
     
     💡 Как вводить:
     • Название станции (например, "Москва-Пассажирская")
     • Код станции (например, "s1234567")
     
     Пожалуйста, введите название или код вашей базовой станции:

User: Podolsk

Bot: Найдено 3 станций. Пожалуйста, выберите вашу базовую станцию:
     [Buttons with station options]

User: [Selects Podolsk - s9600731]

Bot: ✅ Базовая станция успешно установлена!
     🎯 Следующий шаг: Пожалуйста, введите станцию назначения

User: Tsaritsyno

Bot: [Shows confirmation]
     ✅ Подтвердите настройки станций
     ...

User: [Confirms]

Bot: 🎉 Станции успешно сохранены!
```

---

### Step 2: Search for Rides

#### Scenario A: Going to Work/Destination

```
User: /goto

Bot: ⏳ Ищу поезда и попутчиков...

Bot: ✅ Поиск завершен!
     Найдено 8 поездов в ближайший час.
     
     Пока попутчиков не найдено. Мы уведомим вас, когда кто-то найдется!
```

#### Scenario B: Finding Matches

```
User: /goto

Bot: ⏳ Ищу поезда и попутчиков...

Bot: ✅ Поиск завершен!
     Найдено 8 поездов в ближайший час.
     
     🎉 Найдены попутчики!
     
     🚂 Поезд: RU_723Y_... (отправление: 08:45)
     👤 Ivan Petrov (Silikatnaya → Tsaritsyno)
     👤 Maria Ivanova (Podolsk → Tekstilschiki)
     
     🚂 Поезд: RU_823Y_... (отправление: 09:15)
     👤 Alexey Sidorov (Shcherbinka → Tsaritsyno)
```

#### Scenario C: Going Back Home

```
User: /goback

Bot: ⏳ Ищу поезда и попутчиков...

Bot: ✅ Поиск завершен!
     Найдено 6 поездов в ближайший час.
     
     🎉 Найдены попутчики!
     
     🚂 Поезд: RU_724Y_... (отправление: 18:30)
     👤 Dmitry Kozlov (Tekstilschiki → Podolsk)
```

---

### Step 3: Cancel Search (Optional)

```
User: /cancelride

Bot: ✅ Ваш поиск попутчиков отменен.
```

Or if no active search:

```
User: /cancelride

Bot: У вас нет активных поисков попутчиков.
```

---

## Real-World Scenarios

### Scenario 1: Morning Commute

**8:00 AM - Alice searches**
```
Alice: /goto
Bot: Found 12 trains, no matches yet
```

**8:05 AM - Bob searches**
```
Bob: /goto
Bot: Found 10 trains
     🎉 Match: Train at 08:45 with Alice!
```

**8:10 AM - Charlie searches**
```
Charlie: /goto
Bot: Found 11 trains
     🎉 Matches:
     - Train at 08:45 with Alice & Bob
     - Train at 09:15 with Diana
```

Now Alice and Bob see Charlie when they search again!

---

### Scenario 2: Evening Commute (Reverse Direction)

**17:00 PM - Users search to go home**
```
Alice: /goback    (Tsaritsyno → Podolsk)
Bob: /goback      (Tsaritsyno → Silikatnaya)
Charlie: /goback  (Tekstilschiki → Podolsk)
```

Even though they have different stations, they match on trains that serve all their routes!

---

### Scenario 3: Cancellation

**8:00 AM - Alice searches**
```
Alice: /goto
Bot: Found 10 trains, matches with Bob & Charlie on train at 08:45
```

**8:15 AM - Bob cancels**
```
Bob: /cancelride
Bot: Search cancelled
```

**8:20 AM - Alice searches again**
```
Alice: /goto
Bot: Found 10 trains, matches with Charlie on train at 08:45
     (Bob no longer shown - he cancelled)
```

---

### Scenario 4: Automatic Expiration

**8:00 AM - Alice searches**
```
Alice: /goto
Bot: Stored search with TTL: 1 hour
```

**10:30 AM - TTL expires**
```
MongoDB automatically deletes Alice's search
Alice no longer appears in other users' matches
```

**10:35 AM - Bob searches**
```
Bob: /goto
Bot: Found matches, but Alice not included (her search expired)
```

---

## Edge Cases

### Case 1: No Stations Configured
```
User: /goto
Bot: ⚠️ Сначала установите станции с помощью /setstations!
```

### Case 2: No Trains in Time Window
```
User: /goto
Bot: ⏳ Ищу поезда и попутчиков...
Bot: ❌ Поездов не найдено в ближайший час.
```

### Case 3: API Error
```
User: /goto
Bot: ⏳ Ищу поезда и попутчиков...
Bot: ❌ Не удалось выполнить поиск. Попробуйте позже.
```

---

## Command Reference

### /goto
**Purpose**: Search for trains from your base station to destination  
**Time Window**: Next 1 hour from now  
**Caching**: Uses cached schedule data when available  
**Matching**: Finds other users with same train threads  
**Storage**: Saves results for 1 hour with TTL  

### /goback
**Purpose**: Search for trains from your destination back to base (reverse)  
**Time Window**: Next 1 hour from now  
**Caching**: Uses cached schedule data when available  
**Matching**: Finds other users with same train threads  
**Storage**: Saves results for 1 hour with TTL  

### /cancelride
**Purpose**: Cancel your active ride search  
**Effect**: Removes you from matching pool immediately  
**Note**: Other users won't see you in their matches anymore  

---

## Tips

1. **Search Multiple Times**: 
   - Search periodically to see new matches
   - Other users may join after your initial search

2. **Use Both Directions**:
   - Use `/goto` in the morning
   - Use `/goback` in the evening

3. **Plan Ahead**:
   - Search window is 1 hour
   - Search when you're ready to commit to a time range

4. **Cancel When Plans Change**:
   - Use `/cancelride` if your plans change
   - Prevents other users from seeing outdated matches

5. **Check Your Profile**:
   - Use `/profile` to verify your stations
   - Update with `/setstations` if needed

---

## Troubleshooting

**Q: Why don't I see any matches?**  
A: No other users have searched for trains that overlap with yours in the same time window.

**Q: Can I match with users going to different destinations?**  
A: Yes! The system matches by train thread, not destination. If two users take the same physical train (even to different stops), they'll match.

**Q: How long do matches last?**  
A: Matches expire after 1 hour automatically via MongoDB TTL.

**Q: Can I search for multiple time windows?**  
A: Each search replaces your previous search. The system always shows trains for the next 1 hour from when you search.

**Q: What if I need to change my stations?**  
A: Currently, station updates are restricted after initial setup. Contact an admin for changes.
