import asyncio
from tcputils import *

from os import urandom
from math import ceil

class Servidor:
    def __init__(self, rede, porta):
        self.rede = rede
        self.porta = porta
        self.conexoes = {}
        self.callback = None
        self.rede.registrar_recebedor(self._rdt_rcv)

    def registrar_monitor_de_conexoes_aceitas(self, callback):
        """
        Usado pela camada de aplicação para registrar uma função para ser chamada
        sempre que uma nova conexão for aceita
        """
        self.callback = callback

    def _rdt_rcv(self, src_addr, dst_addr, segment):
        src_port, dst_port, seq_no, ack_no, \
            flags, window_size, checksum, urg_ptr = read_header(segment)

        if dst_port != self.porta:
            # Ignora segmentos que não são destinados à porta do nosso servidor
            return
        if not self.rede.ignore_checksum and calc_checksum(segment, src_addr, dst_addr) != 0:
            print('descartando segmento com checksum incorreto')
            return

        payload = segment[4*(flags>>12):]
        id_conexao = (src_addr, src_port, dst_addr, dst_port)

        if (flags & FLAGS_SYN) == FLAGS_SYN:
            # A flag SYN estar setada significa que é um cliente tentando estabelecer uma conexão nova
            # TODO: talvez você precise passar mais coisas para o construtor de conexão
            conexao = self.conexoes[id_conexao] = Conexao(self, id_conexao, seq_no, ack_no)
            # TODO: você precisa fazer o handshake aceitando a conexão. Escolha se você acha melhor
            # fazer aqui mesmo ou dentro da classe Conexao.

            #### Step 1
           # Acho que pode deixar a verificação do passo 1 aqui mesmo
            seq_enviar = int(urandom(2).hex(), 16)
            ack_enviar = seq_no + 1
            segment = make_header(dst_port, src_port, seq_enviar, ack_enviar, FLAGS_SYN | FLAGS_ACK)
            response = fix_checksum(segment, dst_addr, src_addr)
            self.rede.enviar(response, src_addr)

            if self.callback:
                self.callback(conexao)
        elif id_conexao in self.conexoes:
            # Passa para a conexão adequada se ela já estiver estabelecida
            #print('ack:', ack_no)
            self.conexoes[id_conexao]._rdt_rcv(seq_no, ack_no, flags, payload)

        else:
            print('%s:%d -> %s:%d (pacote associado a conexão desconhecida)' %
                  (src_addr, src_port, dst_addr, dst_port))


class Conexao:
    def __init__(self, servidor, id_conexao, seq_no, ack_no):
        self.servidor = servidor
        self.id_conexao = id_conexao
        self.callback = None
        self.timer = asyncio.get_event_loop().call_later(1, self._exemplo_timer)  # um timer pode ser criado assim; esta linha é só um exemplo e pode ser removida
        #self.timer.cancel()   # é possível cancelar o timer chamando esse método; esta linha é só um exemplo e pode ser removida

        self.expected_seq_no = seq_no + 1
        self.seq_enviar = int(urandom(2).hex(), 16)
       # self.my_len_seq_no = 0
        self.my_len_seq_no = ack_no
        
    def _exemplo_timer(self):
        # Esta função é só um exemplo e pode ser removida
        print('Este é um exemplo de como fazer um timer')

    def _rdt_rcv(self, seq_no, ack_no, flags, payload):
        # TODO: trate aqui o recebimento de segmentos provenientes da camada de rede.
        # Chame self.callback(self, dados) para passar dados para a camada de aplicação após
        # garantir que eles não sejam duplicados e que tenham sido recebidos em ordem.
        print('recebido payload: %r' % payload)
        #print(len(payload))
        #print(seq_no)
        #print(self.expected_seq_no)
        
      #### Step 2: verificar número de sequência esperado
      #A verificação e o incremento de numero esperado estão corretos
      #TODO: falta chamar a callback(self,dados)

        if(seq_no == self.expected_seq_no):
          self.expected_seq_no += (len(payload) if payload else 0)
          self.callback(self, payload)
          self.my_len_seq_no = ack_no
          if((flags & FLAGS_ACK == FLAGS_ACK) & (len(payload) > 0)):
            src_addr, src_port, dst_addr, dst_port = self.id_conexao   
            segment = make_header(dst_port, src_port, self.seq_enviar, self.expected_seq_no, flags)
            response = fix_checksum(segment, dst_addr, src_addr)
            print('rdt_rcv')
            self.servidor.rede.enviar(response, src_addr)
            
        #  print(self.cur_ack_no)
          
     
    # Os métodos abaixo fazem parte da API

    def registrar_recebedor(self, callback):
        """
        Usado pela camada de aplicação para registrar uma função para ser chamada
        sempre que dados forem corretamente recebidos
        """
        self.callback = callback

    def enviar(self, dados):
        """
        Usado pela camada de aplicação para enviar dados
        """
        # TODO: implemente aqui o envio de dados.
        # Chame self.servidor.rede.enviar(segmento, dest_addr) para enviar o segmento
        # que você construir para a camada de rede.
        src_addr, src_port, dst_addr, dst_port = self.id_conexao  
        #if dados:
          #segment = make_header(dst_port, src_port, self.seq_enviar, self.expected_seq_no, FLAGS_ACK)
          #response = fix_checksum(segment, dst_addr, src_addr)
          #self.servidor.rede.enviar(response, src_addr)
        size = ceil(len(dados)/MSS)
        for i in range(size):
            #print(i)
            self.seq_enviar = self.my_len_seq_no
            segment = make_header(dst_port, src_port, self.seq_enviar, self.expected_seq_no, flags = FLAGS_ACK)           
            segment += (dados[i*MSS:min((i+1)*MSS, len(dados))])
            self.my_len_seq_no += len(dados[i*MSS:min((i+1)*MSS, len(dados))])
            response = fix_checksum(segment, dst_addr, src_addr)
            self.servidor.rede.enviar(response, src_addr)
            #self.seq_enviar = self.my_len_seq_no
        #print('my_len_seq_no:', self.my_len_seq_no)      

    def fechar(self):
        """
        Usado pela camada de aplicação para fechar a conexão
        """
        # TODO: implemente aqui o fechamento de conexão
        pass

