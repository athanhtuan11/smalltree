from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)

# from app import create_app
# app = create_app()
# from app.models import db
# with app.app_context():
#     db.create_all()