import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

public class GenerateAdminPassword {
    public static void main(String[] args) {
        BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();
        
        // Generate password hash for 'admin123'
        String password = "admin123";
        String hashedPassword = encoder.encode(password);
        
        System.out.println("Password: " + password);
        System.out.println("BCrypt Hash: " + hashedPassword);
        System.out.println("\nSQL to create admin user:");
        System.out.println("INSERT INTO sys_user (id, username, password, super_admin, status, create_date, creator)");
        System.out.println("VALUES (1, 'admin', '" + hashedPassword + "', 1, 1, NOW(), 1);");
    }
}