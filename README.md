# gerapauta :incoming_envelope:
  Pequeno script que busca pautas (de forma paralela) onde o MPT é parte (pólo passivo ou ativo) em audiências do TRT6.

# uso básico
  
  Aconselha-se criar um ambiente virtual Python com as dependências descritas no arquivo **requirements.txt**.
  
  Após carregar o ambiente virtual (algo como source meuambientepython/bin/activate) basta executar **python gerapauta `data'**, 
  data em formato **dd/mm/aaaa.**
  
  O script busca todos os resultados em json do site do TRT6 https://pje.trt6.jus.br/consultaprocessual/pautas
  de forma paralela pois ao todo existem mais de 100 varas no primeiro grau e 9 turmas no segundo grau, cada uma delas
  com pautas de cada dia da semana totalizando mais de 500 pautas que podem ter mais de 50 processos a serem julgados por dia
  o que torna a busca simples do arquivo json muito lenta.
  
  No script original enviamos a mensagem para um grupo do TEAMS para que seja importado para no sistema interno do MPT local.
  
  
