from flask import jsonify, request
from db import session
from models import Product


def init_api_routes(app):
    # GET todos los productos
    @app.route('/api/products', methods=['GET'])
    def get_products():
        products = session.query(Product).all()
        products_list = []
        for product in products:
            products_list.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'category': product.category
            })
        return jsonify(products_list), 200

    # GET un producto por ID
    @app.route('/api/product/<int:product_id>', methods=['GET'])
    def get_product_by_id(product_id):
        product = session.query(Product).filter(Product.id == product_id).first()

        if product is None:
            return jsonify({"error": "Not Found"}), 404

        return jsonify({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'category': product.category
        }), 200

    # POST crear producto
    @app.route('/api/product', methods=['POST'])
    def post_product():
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validación básica
        name = data.get('name')
        price = data.get('price')
        category = data.get('category')

        if not name or price is None or not category:
            return jsonify({"error": "name, price and category are required"}), 400

        new_product = Product(
            name=name,
            price=price,
            category=category
        )

        session.add(new_product)
        session.commit()

        return jsonify({
            'id': new_product.id,
            'name': new_product.name,
            'price': new_product.price,
            'category': new_product.category
        }), 201

    # PUT actualizar producto
    @app.route('/api/product/<int:product_id>', methods=['PUT'])
    def put_product(product_id):
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        product = session.query(Product).filter(Product.id == product_id).first()

        if product is None:
            return jsonify({"error": "Not Found"}), 404

        product.name = data.get("name", product.name)
        product.price = data.get("price", product.price)
        product.category = data.get("category", product.category)

        session.commit()

        return jsonify({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'category': product.category
        }), 200

    # DELETE eliminar producto
    @app.route('/api/product/<int:product_id>', methods=['DELETE'])
    def delete_product(product_id):
        product = session.query(Product).filter(Product.id == product_id).first()

        if product is None:
            return jsonify({"error": "Not Found"}), 404

        session.delete(product)
        session.commit()

        # 204 sin contenido
        return '', 204