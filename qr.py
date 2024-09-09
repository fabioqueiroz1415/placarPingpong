from app import generate_qr_rota, show_qr_code_in_thread

if __name__ == '__main__':
    show_qr_code_in_thread(generate_qr_rota("/links"), "/links", 10000)