package com.example.demo;

import jakarta.persistence.*;
import lombok.*;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.servlet.ServletRegistrationBean;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.core.io.ClassPathResource;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.ws.config.annotation.EnableWs;
import org.springframework.ws.server.endpoint.annotation.*;
import org.springframework.ws.transport.http.MessageDispatcherServlet;
import org.springframework.ws.wsdl.wsdl11.DefaultWsdl11Definition;
import org.springframework.xml.xsd.SimpleXsdSchema;
import org.springframework.xml.xsd.XsdSchema;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

import javax.xml.parsers.DocumentBuilderFactory;
import java.util.List;

@SpringBootApplication
@EnableWs
public class SoapApplication {
    public static void main(String[] args) {
        SpringApplication.run(SoapApplication.class, args);
    }

    @Bean
    public ServletRegistrationBean<MessageDispatcherServlet> messageDispatcherServlet(ApplicationContext applicationContext) {
        MessageDispatcherServlet servlet = new MessageDispatcherServlet();
        servlet.setApplicationContext(applicationContext);
        servlet.setTransformWsdlLocations(true);
        return new ServletRegistrationBean<>(servlet, "/ws/*");
    }

    @Bean(name = "users")
    public DefaultWsdl11Definition defaultWsdl11Definition(XsdSchema usersSchema) {
        DefaultWsdl11Definition wsdl11Definition = new DefaultWsdl11Definition();
        wsdl11Definition.setPortTypeName("UsersPort");
        wsdl11Definition.setLocationUri("/ws");
        wsdl11Definition.setTargetNamespace("http://example.com/demo");
        wsdl11Definition.setSchema(usersSchema);
        return wsdl11Definition;
    }

    @Bean
    public XsdSchema usersSchema() {
        return new SimpleXsdSchema(new ClassPathResource("users.xsd"));
    }
}

@Entity @Table(name = "users")
@Data @NoArgsConstructor @AllArgsConstructor
class User {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String name;
    private Integer age;

    @OneToMany(mappedBy = "user", fetch = FetchType.EAGER)
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
    private User user;

    @ManyToMany(fetch = FetchType.EAGER)
    @JoinTable(
        name = "playlist_songs",
        joinColumns = @JoinColumn(name = "playlist_id"),
        inverseJoinColumns = @JoinColumn(name = "song_id")
    )
    private List<Song> songs;
}

@Entity @Table(name = "songs")
@Data @NoArgsConstructor @AllArgsConstructor
class Song {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String title;
    private String artist;

    @ManyToMany(mappedBy = "songs", fetch = FetchType.LAZY)
    private List<Playlist> playlists;
}

interface UserRepository extends JpaRepository<User, Long> {}

interface PlaylistRepository extends JpaRepository<Playlist, Long> {
    List<Playlist> findByUserId(Long userId);
    List<Playlist> findBySongsId(Long songId);
}

interface SongRepository extends JpaRepository<Song, Long> {
    List<Song> findByPlaylistsId(Long playlistId);
}

@Endpoint
@RequiredArgsConstructor
class UserEndpoint {
    private final UserRepository userRepo;
    private final PlaylistRepository playlistRepo;
    private final SongRepository songRepo;
    private static final String NS = "http://example.com/demo";

    // 1. Listar os dados de todos os usuários do serviço
    @PayloadRoot(namespace = NS, localPart = "getAllUsersRequest")
    @ResponsePayload
    public Element getAllUsers(@RequestPayload Element req) {
        return buildResponse("getAllUsersResponse", "users", userRepo.findAll());
    }

    // 2. Listar os dados de todas as músicas mantidas pelo serviço
    @PayloadRoot(namespace = NS, localPart = "getAllSongsRequest")
    @ResponsePayload
    public Element getAllSongs(@RequestPayload Element req) {
        return buildResponse("getAllSongsResponse", "songs", songRepo.findAll());
    }

    // 3. Listar os dados de todas as playlists de um determinado usuário
    @PayloadRoot(namespace = NS, localPart = "getUserPlaylistsRequest")
    @ResponsePayload
    public Element getUserPlaylists(@RequestPayload Element req) {
        String idText = req.getElementsByTagNameNS(NS, "userId").item(0).getTextContent();
        long id = Long.parseLong(idText);
        return buildResponse("getUserPlaylistsResponse", "playlists", playlistRepo.findByUserId(id));
    }

    // 4. Listar os dados de todas as músicas de uma determinada playlist
    @PayloadRoot(namespace = NS, localPart = "getPlaylistSongsRequest")
    @ResponsePayload
    public Element getPlaylistSongs(@RequestPayload Element req) {
        String idText = req.getElementsByTagNameNS(NS, "playlistId").item(0).getTextContent();
        long id = Long.parseLong(idText);
        return buildResponse("getPlaylistSongsResponse", "songs", songRepo.findByPlaylistsId(id));
    }

    // 5. Listar os dados de todas as playlists que contêm uma determinada música
    @PayloadRoot(namespace = NS, localPart = "getPlaylistsBySongRequest")
    @ResponsePayload
    public Element getPlaylistsBySong(@RequestPayload Element req) {
        String idText = req.getElementsByTagNameNS(NS, "songId").item(0).getTextContent();
        long id = Long.parseLong(idText);
        return buildResponse("getPlaylistsBySongResponse", "playlists", playlistRepo.findBySongsId(id));
    }

    private Element buildResponse(String rootName, String itemName, List<?> items) {
        try {
            Document doc = DocumentBuilderFactory.newInstance().newDocumentBuilder().newDocument();
            Element root = doc.createElementNS(NS, rootName);
            
            for (Object obj : items) {
                if (itemName.equals("users")) appendUser(doc, root, (User) obj);
                else if (itemName.equals("songs")) appendSong(doc, root, (Song) obj);
                else if (itemName.equals("playlists")) appendPlaylist(doc, root, (Playlist) obj);
            }
            return root;
        } catch (Exception e) { throw new RuntimeException(e); }
    }

    private void appendUser(Document doc, Element root, User u) {
        Element el = doc.createElementNS(NS, "users");
        addNode(doc, el, "id", str(u.getId()));
        addNode(doc, el, "name", u.getName());
        addNode(doc, el, "age", str(u.getAge()));
        root.appendChild(el);
    }

    private void appendSong(Document doc, Element root, Song s) {
        Element el = doc.createElementNS(NS, "songs");
        addNode(doc, el, "id", str(s.getId()));
        addNode(doc, el, "title", s.getTitle());
        addNode(doc, el, "artist", s.getArtist());
        root.appendChild(el);
    }
    
    private void appendPlaylist(Document doc, Element root, Playlist p) {
        Element el = doc.createElementNS(NS, "playlists");
        addNode(doc, el, "id", str(p.getId()));
        addNode(doc, el, "name", p.getName());
        if(p.getSongs() != null) {
             for(Song s : p.getSongs()) appendSong(doc, el, s);
        }
        root.appendChild(el);
    }

    private void addNode(Document doc, Element parent, String name, String val) {
        Element e = doc.createElementNS(NS, name); 
        e.setTextContent(val != null ? val : ""); 
        parent.appendChild(e);
    }
    
    private String str(Object o) { return String.valueOf(o); }
}
