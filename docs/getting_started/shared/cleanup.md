## Cleanup (Optional)

You have reached the end of the tutorial! If you are planning to rerun any of the tutorials, don't forget to cleanup:

- To shut down the server: press `CTRL`+`C` in the terminal where the server is running.

- To cleanup the downloaded files workspace (make sure you are in the MedPerf's root directory):

```bash
rm -fr medperf_tutorial
```

- To cleanup the server database: (make sure you are in the MedPerf's root directory)

```bash
cd server
sh reset_db.sh
```

- To cleanup the test storage:

```bash
rm -fr ~/.medperf/localhost_8000
```
