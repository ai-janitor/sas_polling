# DataFit Debug Strategy Notes

## Debugging Workflow
1. **Check docker compose logs** - First line of defense for container issues
2. **Check individual container logs** - `docker logs <container-name>`
3. **Check service health endpoints** - `/health` on each service
4. **Check API responses** - Direct curl tests to isolate frontend vs backend
5. **Check network connectivity** - Ensure services can reach each other
6. **Check configuration** - Verify environment variables are loaded correctly

## Common Issues & Solutions

### Container Issues
- **Container not starting**: Check `docker logs <container>` for startup errors
- **Port conflicts**: Use sequential port mapping (8100-8102) 
- **Network issues**: Ensure all containers on same Docker network
- **Permission issues**: Check non-root user setup in Dockerfiles

### API Issues  
- **HTTP 422**: Payload validation mismatch - check request structure
- **HTTP 503**: Service unavailable - check dependent services health
- **HTTP 404**: Endpoint not found - verify URL paths and nginx proxy config
- **CORS errors**: Check CORS headers in backend responses

### Frontend Issues
- **JavaScript errors**: Check browser console for line numbers
- **Missing assets**: Verify build script copies all files correctly
- **Form validation**: Check data structure matches backend expectations
- **Navigation errors**: Verify DOM element IDs match JavaScript selectors

## Configuration Notes
- **Ports changed**: SUBMISSION_PORT updated to 5050 internally
- **External ports**: GUI=8100, Submission=8101, Polling=8102  
- **Internal ports**: GUI=3000, Submission=5050, Polling=5001
- **Service communication**: Uses internal Docker network with standard ports

## Current Status
- GUI: Running on port 8100 (nginx + SPA)
- Job Submission: Should run on port 5050 internally, 8101 externally
- Job Polling: Running on port 5001 internally, 8102 externally

## Debug Commands
```bash
# Check all containers
docker ps -a --filter "name=datafit"

# Check container logs
docker logs <container-name>

# Check service health
curl http://localhost:8100/health  # GUI
curl http://localhost:8101/health  # Submission  
curl http://localhost:8102/health  # Polling

# Test API directly
curl -X POST http://localhost:8101/api/jobs -H "Content-Type: application/json" -d '{...}'

# Check Docker network
docker network ls
docker network inspect datafit-network
```

## Issue Resolution Log
- ✅ Fixed nginx configuration for Docker networking
- ✅ Fixed JavaScript data structure for subcategories
- ✅ Fixed form generator schema validation
- ✅ Added minimal typing UX (date pickers, number inputs)
- 🔄 **Current**: Job submission payload structure (HTTP 422 error)