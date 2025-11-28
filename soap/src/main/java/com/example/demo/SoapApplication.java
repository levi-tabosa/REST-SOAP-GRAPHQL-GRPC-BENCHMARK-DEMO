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
    private String email;

    @OneToMany(mappedBy = "user", fetch = FetchType.EAGER)
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
    private User user;

    @OneToMany(mappedBy = "playlist", fetch = FetchType.EAGER)
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
    private Playlist playlist;
}

interface UserRepository extends JpaRepository<User, Long> {}

@Endpoint
@RequiredArgsConstructor
class UserEndpoint {
    private final UserRepository repository;
    private static final String NAMESPACE_URI = "http://example.com/demo";

    @PayloadRoot(namespace = NAMESPACE_URI, localPart = "getUserRequest")
    @ResponsePayload
    public Element getUser(@RequestPayload Element request) {
        String idStr = request.getElementsByTagNameNS(NAMESPACE_URI, "id").item(0).getTextContent();
        
        // Fetch
        User user = repository.findById(Long.parseLong(idStr)).orElseThrow();

        try {
            // Cronstrua a resposta declarativamente
            Document doc = DocumentBuilderFactory.newInstance().newDocumentBuilder().newDocument();
            Element response = doc.createElementNS(NAMESPACE_URI, "getUserResponse");

            Element id = doc.createElementNS(NAMESPACE_URI, "id"); id.setTextContent(String.valueOf(user.getId()));
            Element name = doc.createElementNS(NAMESPACE_URI, "name"); name.setTextContent(user.getName());
            Element email = doc.createElementNS(NAMESPACE_URI, "email"); email.setTextContent(user.getEmail());
            
            response.appendChild(id); response.appendChild(name); response.appendChild(email);

            // Playlists
            if (user.getPlaylists() != null) {
                for (Playlist p : user.getPlaylists()) {
                    Element pElem = doc.createElementNS(NAMESPACE_URI, "playlists");
                    
                    Element pId = doc.createElementNS(NAMESPACE_URI, "id"); pId.setTextContent(String.valueOf(p.getId()));
                    Element pTitle = doc.createElementNS(NAMESPACE_URI, "title"); pTitle.setTextContent(p.getTitle());
                    pElem.appendChild(pId); pElem.appendChild(pTitle);

                    // Songs
                    if (p.getSongs() != null) {
                        for (Song s : p.getSongs()) {
                            Element sElem = doc.createElementNS(NAMESPACE_URI, "songs");
                            Element sTitle = doc.createElementNS(NAMESPACE_URI, "title"); sTitle.setTextContent(s.getTitle());
                            Element sArtist = doc.createElementNS(NAMESPACE_URI, "artist"); sArtist.setTextContent(s.getArtist());
                            sElem.appendChild(sTitle); sElem.appendChild(sArtist);
                            pElem.appendChild(sElem);
                        }
                    }
                    response.appendChild(pElem);
                }
            }
            return response;
        } catch (Exception e) { throw new RuntimeException(e); }
    }
}
