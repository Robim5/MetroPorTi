// catálogo de testes 
export const TEST_SECTIONS = [
  {
    id: "inicio",
    label: "Início",
    tests: [
      {
        id: "health",
        title: "API online",
        purpose: "Confirma que o servidor está no ar (local ou Railway).",
        path: "/health",
        needsKey: false,
      },
      {
        id: "docs",
        title: "Swagger",
        purpose: "Documentação técnica de todos os endpoints.",
        path: "/docs",
        needsKey: false,
        openInTab: true,
      },
    ],
  },
  {
    id: "paragens",
    label: "Paragens",
    tests: [
      {
        title: "Listar paragens",
        purpose: "Primeiras paragens da rede (paginação).",
        path: "/stops?page=1&limit=8",
      },
      {
        title: "Pesquisar por nome",
        purpose: "Utilizador escreve o nome -> ex.: «Trindade», «Maia», «Campanhã».",
        path: "/search/stops?q=Trindade",
      },
      {
        title: "Paragens perto (GPS)",
        purpose: "Paragens num raio em metros (útil com localização no telemóvel).",
        path: "/stops/nearby?lat=41.1523&lon=-8.6093&radius_m=1000&limit=8",
      },
      {
        title: "Detalhe de paragem",
        purpose: "Nome, coordenadas e zona tarifária de uma paragem.",
        path: "/stops/5726",
      },
    ],
  },
  {
    id: "horarios",
    label: "Horários",
    tests: [
      {
        title: "Próximas chegadas (Trindade)",
        purpose: "Hub central: costuma mostrar várias linhas e sentidos com minutos até chegar.",
        path: "/stops/5726/next?limit=10",
      },
      {
        title: "Próximas chegadas (outra paragem)",
        purpose: "Mesmo endpoint noutra paragem -> compara resultados (ex. zona Maia).",
        path: "/stops/5760/next?limit=8",
      },
      {
        title: "Filtrar só uma linha",
        purpose: "«Próximo da linha B?» -> usa route_id na paragem onde essa linha passa.",
        path: "/stops/5726/next?limit=8&route_id=B",
      },
      {
        title: "Filtrar por destino",
        purpose:
          "Só metros cujo sentido (trip_headsign) contém o texto. Tem de existir nessa paragem -> testa «Campanhã» no Fórum Maia ou «Póvoa» na Trindade.",
        path: "/stops/5760/arrivals?destination=Campanhã&limit=8",
      },
      {
        title: "Filtrar destino (outro exemplo)",
        purpose: "Mesmo filtro noutra paragem / outro texto de destino.",
        path: "/stops/5726/arrivals?destination=Póvoa&limit=8",
      },
      {
        title: "Painel da estação",
        purpose: "Várias linhas de uma vez: próximas partidas por linha e sentido.",
        path: "/stops/5726/board?per_line=2",
      },
      {
        title: "Horário do dia",
        purpose: "Todas as partidas previstas na paragem, agrupadas por linha.",
        path: "/stops/5726/schedule",
      },
    ],
  },
  {
    id: "linhas",
    label: "Linhas",
    tests: [
      {
        title: "Todas as linhas",
        purpose: "Lista A, B, C, D… com cores para a interface.",
        path: "/routes?limit=10",
      },
      {
        title: "Paragens de uma linha",
        purpose: "Percurso completo de uma linha por ordem (ex. linha B).",
        path: "/lines/B/stops?direction_id=0",
      },
      {
        title: "Outra linha",
        purpose: "Comparar percursos -> ex. linha A.",
        path: "/lines/A/stops?direction_id=0",
      },
      {
        title: "Posição simulada",
        purpose: "Entre que paragens o metro «está» agora (baseado nos horários, não GPS).",
        path: "/vehicle/position?route_id=B",
      },
    ],
  },
  {
    id: "viagens",
    label: "Viagens",
    tests: [
      {
        title: "Viagem directa",
        purpose: "Há alguma viagem sem mudar de metro entre duas paragens?",
        path: "/journey?from_stop_id=5726&to_stop_id=5708",
      },
    ],
  },
  {
    id: "extra",
    label: "Extra",
    tests: [
      {
        title: "Tarifa entre zonas",
        purpose: "Preço entre duas zonas tarifárias do GTFS.",
        path: "/fare?from_zone=PRT1&to_zone=PRT2",
      },
    ],
  },
];
