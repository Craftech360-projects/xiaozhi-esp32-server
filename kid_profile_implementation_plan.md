# Kid Profile Integration: Device-to-Kid Direct Linking

## 🎯 Better Relationship Model

### Scenario: User has 2 kids, 2 toys
- **Kid A (Alice, 7yo)** → **Toy #1** (MAC: aa:bb:cc:dd:ee:ff)
- **Kid B (Bob, 10yo)** → **Toy #2** (MAC: 11:22:33:44:55:66)

### Database Relationship
```
ai_device:
- Add: kid_id column (FK to kid_profile)

Flow: Device MAC → kid_id → Kid Profile
```

## 📊 Updated Database Schema

### Modify ai_device table
```sql
ALTER TABLE ai_device
ADD COLUMN kid_id BIGINT,
ADD FOREIGN KEY (kid_id) REFERENCES kid_profile(id);
```

### kid_profile table (same as before)
```sql
CREATE TABLE kid_profile (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  name VARCHAR(100) NOT NULL,
  date_of_birth DATE NOT NULL,
  gender VARCHAR(20),
  interests TEXT,
  avatar_url VARCHAR(500),
  created_at DATETIME,
  updated_at DATETIME,

  FOREIGN KEY (user_id) REFERENCES sys_user(id)
);
```

## 🔧 Implementation Steps

### Phase 1: Database Changes

**1.1 Update DeviceEntity.java**
```java
@Schema(description = "关联的孩子ID")
private Long kidId;
```

**1.2 Create kid_profile table** (Liquibase migration)

**1.3 No is_active flag needed!** Each device has its assigned kid

### Phase 2: Backend API (Manager API)

**2.1 Create KidProfileService**
- Standard CRUD operations
- `getKidsByUserId(userId)` - list all kids for parent

**2.2 Update DeviceService**
- `assignKidToDevice(deviceId, kidId)` - link kid to device
- Validate: kid belongs to same user who owns device

**2.3 Create API for LiveKit**
```java
@PostMapping("/api/config/child-profile-by-mac")
public Result<ChildProfileDTO> getChildProfileByMac(@RequestBody MacAddressDTO dto) {
    // 1. Get device by MAC
    DeviceEntity device = deviceService.getByMacAddress(dto.getMacAddress());

    // 2. Get kid directly from device.kidId
    if (device.getKidId() == null) {
        return Result.error("No child assigned to this device");
    }

    KidProfileDTO kid = kidProfileService.getById(device.getKidId());

    // 3. Return child profile
    return Result.ok(convertToChildProfile(kid));
}
```

### Phase 3: LiveKit Server

**3.1 Update database_helper.py**
```python
async def get_child_profile_by_mac(self, device_mac: str) -> Optional[dict]:
    """Get child profile assigned to this device"""
    url = f"{self.manager_api_url}/config/child-profile-by-mac"
    payload = {"macAddress": device_mac}
    # Returns: {name, age, ageGroup, gender, interests}
```

**3.2 Update main.py** (same as before)
- Fetch child profile by MAC
- Inject into agent prompt template
- Personalize based on kid's age/interests

### Phase 4: Flutter App

**4.1 Device Management Screen**
- Show list of devices
- For each device: dropdown to select which kid uses it
- Call API: `PUT /api/mobile/devices/{id}/assign-kid`

**4.2 Kid Profile Screen**
- Create/edit kids (name, DOB, interests)
- Show which devices are assigned to this kid

**4.3 API Service**
```dart
// Assign kid to device
Future<bool> assignKidToDevice(String deviceId, String kidId) async {
  final response = await put('/api/mobile/devices/$deviceId/assign-kid',
    body: {'kidId': kidId}
  );
  return response.success;
}
```

## 🎯 User Flow Example

### Setup Phase (in Flutter app):
1. Parent creates 2 kid profiles:
   - Alice (7yo, loves stories)
   - Bob (10yo, loves science)

2. Parent has 2 paired devices:
   - Toy #1 (MAC: aa:bb:cc:dd:ee:ff)
   - Toy #2 (MAC: 11:22:33:44:55:66)

3. Parent assigns:
   - Toy #1 → Alice
   - Toy #2 → Bob

### Runtime Phase (LiveKit):
1. Toy #1 connects → MAC: aa:bb:cc:dd:ee:ff
2. LiveKit queries: MAC → device → kidId → Alice's profile
3. Agent prompt: "Hi Alice! You're 7 years old, want a story?"

4. Toy #2 connects → MAC: 11:22:33:44:55:66
5. LiveKit queries: MAC → device → kidId → Bob's profile
6. Agent prompt: "Hey Bob! You're 10, want science facts?"

## ✅ Advantages of Device-Kid Linking

✅ **Simple & Direct** - One query: MAC → kid_id → profile
✅ **Multi-device, multi-kid** - Each toy knows its kid
✅ **No switching needed** - Automatic based on which toy connects
✅ **Clean separation** - Alice's toy = Alice's experience
✅ **Scalable** - Works with 1 kid or 10 kids, 1 toy or 10 toys

## 📝 API Endpoints Summary

### Manager API
- `POST /api/mobile/kids/create` - create kid profile
- `GET /api/mobile/kids/list` - list kids for user
- `PUT /api/mobile/kids/{id}` - update kid
- `DELETE /api/mobile/kids/{id}` - delete kid
- `PUT /api/mobile/devices/{id}/assign-kid` - link device to kid
- `POST /config/child-profile-by-mac` - get kid by device MAC (for LiveKit)

## 📂 Files to Create/Modify

### Manager API (Java/Spring Boot)
- `xiaozhi/modules/sys/entity/KidProfileEntity.java` - NEW
- `xiaozhi/modules/sys/dao/KidProfileDao.java` - NEW
- `xiaozhi/modules/sys/dao/KidProfileDao.xml` - NEW
- `xiaozhi/modules/sys/dto/KidProfileDTO.java` - NEW
- `xiaozhi/modules/sys/dto/KidProfileCreateDTO.java` - NEW
- `xiaozhi/modules/sys/dto/KidProfileUpdateDTO.java` - NEW
- `xiaozhi/modules/sys/service/KidProfileService.java` - NEW
- `xiaozhi/modules/sys/service/impl/KidProfileServiceImpl.java` - NEW
- `xiaozhi/modules/sys/controller/MobileKidProfileController.java` - NEW
- `xiaozhi/modules/device/entity/DeviceEntity.java` - MODIFY (add kidId)
- `xiaozhi/modules/sys/controller/ConfigController.java` - ADD endpoint

### LiveKit Server (Python)
- `src/utils/database_helper.py` - ADD get_child_profile_by_mac()
- `main.py` - MODIFY entrypoint to fetch & inject child profile
- `config.yaml` - UPDATE prompt template with child variables

### Flutter App (Dart)
- `lib/services/java_kid_profile_service.dart` - NEW
- `lib/services/java_device_service.dart` - ADD assignKidToDevice()
- `lib/screens/kids/kid_profile_screen.dart` - UPDATE to use Java API
- `lib/screens/devices/device_assignment_screen.dart` - NEW

### Database
- Liquibase changelog for kid_profile table - NEW
- Liquibase changelog to add kid_id to ai_device - NEW
