import ffmpeg

def convert_webm_to_mp4(input_file, output_file):
    try:
        ffmpeg.input(input_file).output(output_file).run()
        print(f'Arquivo convertido com sucesso: {output_file}')
    except ffmpeg.Error as e:
        print(f'Erro ao converter o arquivo: {e}')

# Exemplo de uso
input_file = 'roda.webm'  # Caminho do arquivo de entrada
output_file = 'output.mp4'  # Caminho do arquivo de saída

convert_webm_to_mp4(input_file, output_file)
