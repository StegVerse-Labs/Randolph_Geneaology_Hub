"""Keep pytest out of sdk-staging/.

sdk-staging/ holds files destined for StegVerse-org/StegVerse-SDK, kept byte-identical to
what that repository needs so the write there is a copy. Its test imports `stegverse`,
which exists in the SDK and not here, so collecting it in this repository fails. The
staged calculation is still covered here, by tests/test_sdk_worker_cost_binding_staging.py,
which loads the module directly and checks it against the measured record.
"""
collect_ignore_glob = ["sdk-staging/*"]
