/*
   BLAKE2 throughput benchmark for Artemis.

   Times the sse/ implementations of blake2b, blake2s, blake2bp and blake2sp
   over several message sizes and writes artemis_results.json (numeric
   metrics only) to the path given as argv[1].

   Metrics (higher is better unless noted):
     <algo>_<size>_mb_s   median throughput in MB/s (1 MB = 1e6 bytes)
     overall_mb_s         geometric mean of all <algo>_<size>_mb_s
     overall_ns_per_byte  1000 / overall_mb_s (lower is better)
*/
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../sse/blake2.h"

#if defined(_WIN32)
#include <windows.h>
static double now_s( void )
{
  LARGE_INTEGER f, c;
  QueryPerformanceFrequency( &f );
  QueryPerformanceCounter( &c );
  return ( double )c.QuadPart / ( double )f.QuadPart;
}
#else
#include <time.h>
static double now_s( void )
{
  struct timespec ts;
  clock_gettime( CLOCK_MONOTONIC, &ts );
  return ts.tv_sec + ts.tv_nsec * 1e-9;
}
#endif

typedef int ( *hash_fn )( void *, size_t, const void *, size_t, const void *, size_t );

static const struct { const char *name; hash_fn fn; size_t outlen; } ALGOS[] = {
  { "blake2b",  blake2b,  BLAKE2B_OUTBYTES },
  { "blake2s",  blake2s,  BLAKE2S_OUTBYTES },
  { "blake2bp", blake2bp, BLAKE2B_OUTBYTES },
  { "blake2sp", blake2sp, BLAKE2S_OUTBYTES },
};

static const struct { const char *label; size_t len; } SIZES[] = {
  { "64b",  64 },
  { "1kb",  1024 },
  { "64kb", 65536 },
  { "1mb",  1048576 },
};

#define NALGOS  ( sizeof( ALGOS ) / sizeof( ALGOS[0] ) )
#define NSIZES  ( sizeof( SIZES ) / sizeof( SIZES[0] ) )
#define TRIALS  9
#define BYTES_PER_TRIAL ( 32u * 1024u * 1024u )  /* ~32 MB hashed per trial */

static int cmp_double( const void *x, const void *y )
{
  double a = *( const double * )x, b = *( const double * )y;
  return ( a > b ) - ( a < b );
}

int main( int argc, char **argv )
{
  const char *out_path = argc > 1 ? argv[1] : "artemis_results.json";
  size_t maxlen = SIZES[NSIZES - 1].len;
  unsigned char *in = malloc( maxlen );
  unsigned char digest[BLAKE2B_OUTBYTES];
  unsigned sink = 0;
  double results[NALGOS][NSIZES];
  double log_sum = 0.0, overall;
  size_t a, s, i;
  FILE *f;

  if( !in ) return 1;
  for( i = 0; i < maxlen; ++i ) in[i] = ( unsigned char )( i * 131 + 7 );

  for( a = 0; a < NALGOS; ++a ) {
    for( s = 0; s < NSIZES; ++s ) {
      size_t len = SIZES[s].len;
      size_t iters = BYTES_PER_TRIAL / len;
      double tp[TRIALS];
      int t;

      /* warm-up */
      for( i = 0; i < iters / 8 + 1; ++i ) {
        ALGOS[a].fn( digest, ALGOS[a].outlen, in, len, NULL, 0 );
        sink += digest[0];
      }

      for( t = 0; t < TRIALS; ++t ) {
        double t0 = now_s(), dt;
        for( i = 0; i < iters; ++i ) {
          if( ALGOS[a].fn( digest, ALGOS[a].outlen, in, len, NULL, 0 ) < 0 ) {
            fprintf( stderr, "%s failed\n", ALGOS[a].name );
            return 1;
          }
          sink += digest[0];
        }
        dt = now_s() - t0;
        tp[t] = ( double )iters * len / dt / 1e6;
      }

      qsort( tp, TRIALS, sizeof( double ), cmp_double );
      results[a][s] = tp[TRIALS / 2];
      log_sum += log( results[a][s] );
      printf( "%-9s %-5s %10.1f MB/s\n", ALGOS[a].name, SIZES[s].label, results[a][s] );
    }
  }

  overall = exp( log_sum / ( NALGOS * NSIZES ) );
  printf( "overall   %10.1f MB/s (geomean)  [sink %u]\n", overall, sink & 1 );

  f = fopen( out_path, "w" );
  if( !f ) { perror( out_path ); return 1; }
  fprintf( f, "{\n" );
  for( a = 0; a < NALGOS; ++a )
    for( s = 0; s < NSIZES; ++s )
      fprintf( f, "  \"%s_%s_mb_s\": %.3f,\n", ALGOS[a].name, SIZES[s].label, results[a][s] );
  fprintf( f, "  \"overall_ns_per_byte\": %.5f,\n", 1000.0 / overall );
  fprintf( f, "  \"overall_mb_s\": %.3f\n}\n", overall );
  if( fclose( f ) != 0 ) return 1;

  free( in );
  return 0;
}
