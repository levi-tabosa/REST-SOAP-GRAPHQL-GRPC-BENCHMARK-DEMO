package com.example.demo;

import com.fasterxml.jackson.annotation.JsonBackReference;
import com.fasterxml.jackson.annotation.JsonManagedReference;
import jakarta.persistence.*;
import lombok.*;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@SpringBootApplication
public class DemoApplication {
    public static void main(String[] args) {
        SpringApplication.run(DemoApplication.class, args);
    }
}

// --- Entities ---
@Entity @Table(name = "users")
@Data @NoArgsConstructor @AllArgsConstructor
class User {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String name;
    private String email;

    @OneToMany(mappedBy = "user", fetch = FetchType.LAZY)
    @JsonManagedReference // Prevent infinite recursion
    @ToString.Exclude     // Prevent stackoverflow in logs
    private List<Playlist> playlists;
}

@Entity @Table(name = "playlists")
@Data @NoArgsConstructor @AllArgsConstructor
class Playlist {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String title;

    @ManyToOne
    @JoinColumn(name = "user_id")
    @JsonBackReference
    @ToString.Exclude
    private User user;

    @OneToMany(mappedBy = "playlist", fetch = FetchType.LAZY)
    @JsonManagedReference
    @ToString.Exclude
    private List<Song> songs;
}

@Entity @Table(name = "songs")
@Data @NoArgsConstructor @AllArgsConstructor
class Song {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String title;
    private String artist;

    @ManyToOne
    @JoinColumn(name = "playlist_id")
    @JsonBackReference
    @ToString.Exclude
    private Playlist playlist;
}

// --- Repository & Controller ---
interface UserRepository extends JpaRepository<User, Long> {}

@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
class UserController {
    private final UserRepository repository;

    @GetMapping
    public List<User> getAll() { 
        return repository.findAll(); 
    }
}
