from app import generate_qr_rota, show_qr_code

show_qr_code(generate_qr_rota("/links"), "/links", 10000)