package com.example.demo;
import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.*;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.MediaType;
import java.util.List;

@SpringBootApplication
public class RestApplication {
    public static void main(String[] args) {
        SpringApplication.run(RestApplication.class, args);
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
    @JsonIgnore
    @ToString.Exclude
    private List<Playlist> playlists;
}


@Entity @Table(name = "playlists")
@Data @NoArgsConstructor @AllArgsConstructor
class Playlist {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;

    @ManyToOne
    @JoinColumn(name = "user_id")
    @JsonIgnore
    private User user;

    @ManyToMany
    @JoinTable(
        name = "playlist_songs",
        joinColumns = @JoinColumn(name = "playlist_id"),
        inverseJoinColumns = @JoinColumn(name = "song_id")
    )
    @JsonIgnore
    private List<Song> songs;
}

@Entity @Table(name = "songs")
@Data @NoArgsConstructor @AllArgsConstructor
class Song {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String title;
    private String artist;

    @ManyToMany(mappedBy = "songs")
    @JsonIgnore
    private List<Playlist> playlists;
}


interface UserRepository extends JpaRepository<User, Long> {}
interface PlaylistRepository extends JpaRepository<Playlist, Long> {
    List<Playlist> findByUserId(Long userId);

    @Query("SELECT p FROM Playlist p JOIN p.songs s WHERE s.id = :songId")
    List<Playlist> findBySongId(@Param("songId") Long songId);
}
interface SongRepository extends JpaRepository<Song, Long> {}


@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
class UserController {

  private final UserRepository repository;
  private final PlaylistRepository playlistRepo;

    // 1. Listar os dados de todos os usuários do serviço
    @GetMapping
    public List<User> getAll() { 
        return repository.findAll(); 
    }

    @GetMapping("/{id}")
    public User getById(@PathVariable Long id) {
        return repository.findById(id).orElseThrow();
    }

    
    @GetMapping("/{id}/playlists")
    public List<Playlist> getUserPlaylists(@PathVariable Long id) { 
        return playlistRepo.findByUserId(id); 
    }



    @PostMapping(consumes = MediaType.ALL_VALUE)
    public User create(@RequestBody User user) {
        return repository.save(user);
    }

    @PutMapping("/{id}")
    public User update(@PathVariable Long id, @RequestBody User newUser) {
        User user = repository.findById(id).orElseThrow();
        user.setName(newUser.getName());
        user.setEmail(newUser.getEmail());
        return repository.save(user);
    }

    @DeleteMapping("/{id}")
    public void delete(@PathVariable Long id) {
        repository.deleteById(id);
    }
}

@RestController
@RequestMapping("/playlists")
@RequiredArgsConstructor
class PlaylistController {

    private final PlaylistRepository repo;
    private final UserRepository userRepo;
    private final SongRepository songRepo;

    @GetMapping
    public List<Playlist> getAll() { return repo.findAll(); }

    @GetMapping("/{id}/songs")
    public List<Song> getPlaylistSongs(@PathVariable Long id) {
        Playlist playlist = repo.findById(id).orElseThrow();
        return playlist.getSongs();
}

    @GetMapping("/search") // ?songId=1
    public List<Playlist> getPlaylistsBySong(@RequestParam Long songId) {
        return repo.findBySongId(songId);
    }

    // 3. Listar os dados de todas as playlists de um determinado usuário
    @PostMapping("/user/{userId}")
    public Playlist createPlaylist(
            @PathVariable Long userId,
            @RequestBody Playlist playlist) {

        User user = userRepo.findById(userId).orElseThrow();
        playlist.setUser(user);
        return repo.save(playlist);
    }

    @PostMapping("/{playlistId}/songs/{songId}")
    public Playlist addSong(
            @PathVariable Long playlistId,
            @PathVariable Long songId) {

        Playlist playlist = repo.findById(playlistId).orElseThrow();
        Song song = songRepo.findById(songId).orElseThrow();

        playlist.getSongs().add(song);
        return repo.save(playlist);
    }
}

@RestController
@RequestMapping("/songs")
@RequiredArgsConstructor
class SongController {

    private final SongRepository repository;

    // 2. Listar os dados de todas as músicas mantidas pelo serviço
    @GetMapping
    public List<Song> getAll() { return repository.findAll(); }

    @PostMapping
    public Song create(@RequestBody Song song) {
        return repository.save(song);
    }
}

