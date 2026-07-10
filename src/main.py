from evals import build_clients, run_full_suite


def main():
    _client, openai_client, credential, model, endpoint, data_dir = build_clients()

    # Register the evals and run the full built-in evaluation suite.
    run_full_suite(openai_client, credential, model, endpoint, data_dir)


if __name__ == "__main__":
    main()
