from app import create_app

app = create_app()


if __name__ == "__main__":
	# Run development server when executed directly for convenience on Windows
	app.run(debug=True)
