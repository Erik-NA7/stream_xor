from flask import Flask, request, jsonify, render_template, Response
import mysql.connector
import base64
import itertools

app = Flask(__name__)

def get_db():
    return mysql.connector.connect(
        host="db",
        user="flaskuser",
        password="flaskpass",
        database="flaskdb"
    )

@app.route("/")
def index():
    return render_template("index.html")
    # return "Flask is Running"

@app.route("/encryption", methods=["POST"])
def encrypt():
    input = request.form["inputText"]
    secret = request.form["key"]
    
# Step 1: Convert input and secret to ASCII decimal
    input_dec = [ord(ch) for ch in input]
    secret_dec = [ord(ch) for ch in secret]

    # Step 2: Convert ASCII decimal to binary (8-bit strings)
    input_bin = [format(code, '08b') for code in input_dec]
    secret_bin = [format(code, '08b') for code in secret_dec]

    # Step 3: XOR operation (cycle the key if shorter than input)
    xor_dec = []
    xor_bin = []

    for i in range(len(input_dec)):
        # cycle the key if shorter than input
        key_val = secret_dec[i % len(secret_dec)]
        result = input_dec[i] ^ key_val
        xor_dec.append(result)
        xor_bin.append(format(result, '08b'))

    # Step 4: Encode ciphertext as Base64
    xor_bytes = bytes(xor_dec)
    xor_b64 = base64.b64encode(xor_bytes).decode()

    # Step 5: Decrypt (XOR ciphertext with the same key)

    output = ''.join(chr(code) for code in xor_dec)
    
    # Step 4: Decrypt (XOR ciphertext with same key again)
    decrypted_chars = []
    for i in range(len(xor_dec)):
        key_val = secret_dec[i % len(secret_dec)]
        decrypted_val = xor_dec[i] ^ key_val
        decrypted_chars.append(chr(decrypted_val))
    decrypted_text = ''.join(decrypted_chars)

    app.logger.info(f"Decrypted Text: {decrypted_text}\n")
    
    # Save to DB
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (input, output, secret_key) VALUES (%s, %s, %s)", (input, xor_b64, secret))
    conn.commit()

    new_id = cursor.lastrowid
    app.logger.info(f"New row ID: {new_id}\n")
    # Fetch the full new row
    cursor.execute("SELECT id, input, output, secret_key FROM messages WHERE id = %s", (new_id,))
    new_row = cursor.fetchone()
    conn.commit()
    conn.close()

    explanation = f"""
Step 1: Input {input} -> ASCII decimals: {input_dec}
Step 2: {input_dec} -> binary (8-bit): {input_bin}
Step 3: Key -> ASCII decimals: {secret_dec}
Step 4: {secret_dec} -> binary (8-bit): {secret_bin}
Step 6: XOR result -> binary (8-bit): {xor_bin}
Step 5: XOR result -> decimals: {xor_dec}
Step 7: Ciphertext -> Base64: {xor_b64}
    """
    output_textarea = f'<textarea id="outputText" class="form-control" rows="8" hx-swap-oob="true">{xor_b64}</textarea>'

    history_row_fragment = f"""
<tr id="row-{new_row[0]}" hx-swap-oob="beforeend" target="#tableBody">
  <td>{new_row[1]}</td>
  <td>{new_row[2]}</td>
  <td>{new_row[3]}</td>
  <td>
    <button class="btn btn-sm btn-danger"
            hx-delete="/history/{new_row[0]}"
            hx-target="closest tr"
            hx-swap="outerHTML">
      <i class="fa-solid fa-trash"></i>
    </button>
  </td>
</tr>
"""
    return output_textarea + history_row_fragment



@app.route("/history")
def history():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, input, output, secret_key FROM messages ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return "".join(
        render_template("row.html", id=id, input=input, output=output, secret_key=secret_key)
        for id, input, output, secret_key in rows
    )


@app.route("/history/<int:id>", methods=["DELETE"])
def delete_history(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE id = %s", (id,))
    conn.commit()
    conn.close()

    return Response("", status=200)


def xor_encrypt(input, key):
    # return "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(text))
    # return bytes([b ^ k for b, k in zip(input, itertools.cycle(key))])
    return bytes([ord(c) ^ ord(key[i % len(key)]) for i, c in enumerate(input)])


def xor_base64(plain: str, key: str) -> str:
    return base64.b64encode(xor_bytes(plain, key)).decode()
