# Comparação de Tecnologias de Invocação de Serviços Remotos  
## REST • SOAP • GraphQL • gRPC  
### Trabalho de Computação Distribuída — Prof. Nabor Mendonça

---

# 1. Equipe

* **Levi Tabosa Costa e Silva** — 2224207
* **Carolina Cavalcante Aguiar** — 2225371
* **Adams Amaral de Castro Filho** — 2220283

---

# 2. Origem, características, vantagens e desvantagens das tecnologias

---

## 2.1. REST

### Origem  
Proposto por Roy Fielding em 2000 como um estilo arquitetural para sistemas distribuídos na web.

### Características  
- Baseado no protocolo HTTP.  
- Utiliza métodos como GET, POST, PUT, DELETE.  
- Modelo stateless.  
- Respostas geralmente em JSON.  

### Vantagens  
- Simplicidade e ampla adoção.  
- Fácil consumo por clientes web e mobile.  
- Baixa curva de aprendizado.  
- Baixa latência na maioria dos cenários.  

### Desvantagens  
- Pode gerar overfetching e underfetching.  
- Não possui um contrato formal como WSDL.  
- Operações podem exigir múltiplas requisições.

---

## 2.2. SOAP

### Origem  
Criado pelo W3C como um padrão formal de comunicação XML adotado em ambientes corporativos.

### Características  
- Baseado em XML.  
- Contrato formal através de WSDL.  
- Suporte a extensões (WS-*).  
- Fortemente tipado.  

### Vantagens  
- Estrutura rígida e padronizada.  
- Suporte nativo a segurança, transações e políticas.  
- Confiável em sistemas corporativos.  

### Desvantagens  
- Respostas pesadas e com alta verbosidade.  
- Latência maior devido ao uso de XML.  
- Implementação mais complexa.

---

## 2.3. GraphQL

### Origem  
Desenvolvido pelo Facebook em 2015.

### Características  
- O cliente define exatamente os campos que deseja.  
- Centralização em uma única rota `/graphql`.  
- Estrutura baseada em esquemas (schema).  

### Vantagens  
- Evita overfetching e underfetching.  
- Reduz o número de requisições.  
- Grande flexibilidade para o cliente.  

### Desvantagens  
- Requisições podem se tornar pesadas.  
- Alto custo computacional.  
- Cache natural menos eficiente.  

---

## 2.4. gRPC

### Origem  
Criado pelo Google em 2015 utilizando HTTP/2 e Protocol Buffers.

### Características  
- Comunicação binária.  
- Contrato via arquivos `.proto`.  
- Suporte a streaming.  
- Alto desempenho.  

### Vantagens  
- Baixíssima latência.  
- Alto throughput.  
- Ideal para microserviços.  

### Desvantagens  
- Debug mais difícil.  
- Não é nativamente amigável ao navegador.  
- Requer ferramentas específicas.

---

# 3. Tecnologias Utilizadas

O projeto foi dividido em duas linguagens de programação para demonstrar interoperabilidade e características específicas de cada tecnologia:

* **Java**: Utilizado para as APIs **REST** e **SOAP**.
* **Python**: Utilizado para as APIs **gRPC** e **GraphQL**.
* **Docker & Docker Compose**: Para orquestração e execução simplificada dos serviços.

## Escopo do Projeto

[cite_start]O sistema simula um serviço de streaming de músicas que gerencia três recursos principais[cite: 20]:
1.  [cite_start]**Usuários** (ID, Nome, Idade) [cite: 22-24]
2.  [cite_start]**Músicas** (ID, Nome, Artista) [cite: 30-32]
3.  [cite_start]**Playlists** (ID, Nome) [cite: 35-36]

### Funcionalidades Implementadas
As quatro tecnologias implementam exatamente o mesmo conjunto de operações:

- Listar usuários  
- Listar músicas  
- Listar playlists de um usuário  
- Listar músicas pertencentes a uma playlist  
- Listar playlists que contêm uma música  

Os serviços compartilham a mesma base de dados (PostgreSQL), garantindo paridade de comportamento entre todas as implementações.


## 4. Como executar

### REST
```bash
docker compose --profile rest up --build
```

### SOAP
```bash
docker compose --profile soap up --build
```

### GraphQL
```bash
docker compose --profile graphql up --build
```

### gRPC
```bash
docker compose --profile grpc up --build
```


## 5. Testes de carga com Locust

Os testes seguem esse padrão:

- 50 usuários simultâneos, executando requisições por 1 minuto;
- 200 usuários simultâneos, executando requisições por 2 minutos;
- 500 usuários simultâneos, executando requisições por 3 minutos.

Em cada cenário, o Locust foi configurado para manter o número de usuários constante durante todo o período de teste, registrando automaticamente métricas de latência (média, p95, p99), throughput (requests por segundo) e quantidade de falhas para cada tecnologia.

Para processar os resultados e gerar gráficos:

```bash
python testes-locust/graficos_locust.py
```

## 6. Gráficos comparativos gerais

- **Latência média**  
  `graficos/latencia_media_por_tech_carga.png`

- **Latência P95**  
  `graficos/latencia_p95_por_tech_carga.png`

- **Requests por segundo (RPS)**  
  `graficos/rps_por_tech_carga.png`

#### REST
- `graficos/rest_latencia.png`  
- `graficos/rest_p95.png`  
- `graficos/rest_rps.png`

#### SOAP
- `graficos/soap_latencia.png`  
- `graficos/soap_p95.png`  
- `graficos/soap_rps.png`

#### GraphQL
- `graficos/graphql_latencia.png`  
- `graficos/graphql_p95.png`  
- `graficos/graphql_rps.png`

#### gRPC
- `graficos/grpc_latencia.png`  
- `graficos/grpc_p95.png`  
- `graficos/grpc_rps.png`

---

## 7. Análise dos resultados

### 7.1. Latência média
- gRPC apresenta o menor tempo médio em todas as cargas.  
- REST mantém-se estável e com boa performance.  
- SOAP apresenta tempos maiores devido ao overhead do XML.  
- GraphQL tem latências elevadas, principalmente em cargas altas.

### 7.2. Latência P95
- gRPC se mantém consistente mesmo a 500 usuários.  
- REST aumenta moderadamente.  
- SOAP cresce significativamente.  
- GraphQL cresce de forma muito acentuada, indicando gargalo.

### 7.3. Requests por segundo (RPS)
- gRPC alcança o maior throughput entre todas as tecnologias.  
- REST também apresenta RPS altos.  
- SOAP e GraphQL possuem throughput inferior.

---

## 8. Conclusão

Resumo da performance observada:

**gRPC > REST > SOAP > GraphQL**

No geral:

- **gRPC** é o mais eficiente, rápido e escalável.  
- **REST** é simples, robusto e performa bem.  
- **SOAP** é estável porém mais pesado.  
- **GraphQL** oferece flexibilidade, mas não se destacou em desempenho.  

---