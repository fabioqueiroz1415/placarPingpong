from app import main, abrir_pagina_web, generate_qr_rota, show_qr_code
import os

if __name__ == '__main__':
    if not os.getenv('WERKZEUG_RUN_MAIN'):  
        abrir_pagina_web("/placar")
        show_qr_code(generate_qr_rota("/links"), "/links", 60000)
    main()